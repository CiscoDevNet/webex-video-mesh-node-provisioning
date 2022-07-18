import re
import requests
import warnings
import subprocess
import csv
import json
from requests.auth import HTTPBasicAuth
from urllib.parse import unquote
from multiprocessing.pool import ThreadPool
from utils import get_rows, mask_passwords

warnings.filterwarnings("ignore")

output = dict()
regex = r"^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"


def worker(*data):
    ip = data[0]
    user = data[1]
    password = data[2]
    external_ip = data[3]
    external_mask = data[4]
    external_gw = data[5]

    if ip not in output:
        output[ip] = dict()
    output[ip]["failure"] = []
    output[ip]["success"] = []
    output[ip]["status"] = "PASS"

    if not re.match(regex, ip):
        process = subprocess.Popen(['nslookup', ip], stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        ret_code = process.returncode
        if ret_code:
            output[ip]["failure"].append("Invalid Video Mesh Node FQDN")
            output[ip]["status"] = "FAIL"
            return

    session = requests.Session()

    # api to get ecp_session cookie
    url_sign_in = "https://" + ip + "/api/v1/auth/signIn"
    headers = {'Content-type': 'application/json', 'Referer': 'https://web.ciscospark.com'}
    url_data = json.dumps({"password": password, "userName": user})
    try:
        request_obj = session.post(url=url_sign_in, verify=False, data=url_data, headers=headers, timeout=60)
    except requests.ConnectTimeout:
        output[ip]["failure"].append("IP does not correspond to a valid VMN.")
        output[ip]["status"] = 'FAIL'
        return
    except requests.ConnectionError:
        output[ip]["failure"].append("Connection refused.")
        output[ip]["status"] = 'FAIL'
        return
    request_obj_json = request_obj.json()
    if request_obj_json["status"]["code"] != 200:
        try:
            message = request_obj_json["result"]["data"]["message"]
        except:
            message = request_obj_json["status"]["message"]
        output[ip]["failure"].append(message)
        output[ip]["status"] = "FAIL"
        return

    ecp_session = request_obj.cookies['ecp_session']

    cookie = "ecp_session=" + ecp_session
    cookie = unquote(cookie)

    auth = HTTPBasicAuth(user, password)
    referer = "https://" + ip + "/setup/"
    api_headers = {'Content-type': 'application/json', "Referer": referer, "Cookie": cookie}

    get_ext_network_url = "https://" + ip + "/api/v1/core/platform/network/external"
    get_request_obj = session.get(url=get_ext_network_url, headers=api_headers, auth=auth, verify=False)
    get_request_obj = get_request_obj.json()
    if get_request_obj['status']['code'] == 200:
        current_ip = get_request_obj['result']['data']['ip']
        # Validating if the current external IP is same as what user has provided as input
        if current_ip == external_ip:
            output[ip]["failure"].append(f"External IP is already {current_ip}")
            output[ip]["status"] = "FAIL"
            return

    external_api_url = "https://" + ip + "/api/v1/core/platform/network/external?skipSave=false&skipReboot=false"
    external_api_data = {
        "externalNetworkEnabled": True,
        "externalIp": external_ip,
        "externalMask": external_mask,
        "externalGateway": external_gw
    }
    external_api_response = session.put(url=external_api_url, data=json.dumps(external_api_data), headers=api_headers,
                                        auth=auth, verify=False)
    external_api_response = external_api_response.json()
    message = external_api_response['result']['data'][0]['message']
    if external_api_response['status']['code'] == 200:
        output[ip]["success"].append(message)
    else:
        output[ip]["failure"].append(message)
        output[ip]["status"] = 'FAIL'


if __name__ == "__main__":
    print('\nAdding external IP\n')
    input_file = "input_external_nw.csv"
    csv_file = open(input_file)
    csv_reader = csv.reader(csv_file)
    cols = next(csv_reader)
    pool = ThreadPool()
    results = {}
    results = {data[0]: pool.apply_async(worker, data) for data in csv_reader if not data[0] == " "}
    pool.close()
    pool.join()
    for i in output:
        print(i, end=':: ')
        if output[i]["failure"]:
            print("Failed:", end=' ')
            for j in output[i]["failure"]:
                print(j)
        if output[i]["success"]:
            print("Successful:", end=' ')
            for j in output[i]["success"]:
                print(j)
    print()
    csv_file.close()

    failed_ips = list()
    passed_ips = list()
    for ip in output:
        if output[ip]['status'] == 'FAIL':
            failed_ips.append(ip)
        else:
            passed_ips.append(ip)

    rows_status = get_rows(input_file, passed_ips, failed_ips, 0)
    if rows_status:
        ret = mask_passwords(input_file, rows_status[0], rows_status[1], col_num=2)
        if ret:
            print("\n Successfully masked the passwords")
        else:
            print("\n Could not mask the passwords")
    else:
        print("\n Could not mask the passwords")

    print('\n')

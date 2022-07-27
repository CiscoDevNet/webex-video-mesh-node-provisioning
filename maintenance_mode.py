import requests
from requests.auth import HTTPBasicAuth
import json
from urllib.parse import unquote
from time import sleep
import csv
import argparse
from multiprocessing.pool import ThreadPool
import re
import warnings
from utils import get_rows
from utils import mask_passwords

warnings.filterwarnings("ignore")

output = []
passed_ips = []
failed_ips = []


def maintenance_mode_on(*data):
    ip = data[0]
    user = data[1]
    password = data[2]

    session = requests.Session()

    # api to get ecp_session cookie

    url_sign_in = "https://" + ip + "/api/v1/auth/signIn"
    headers = {'Content-type': 'application/json', 'Referer': 'https://web.ciscospark.com'}
    url_data = json.dumps({"password": password, "userName": user})
    try:
        request_obj = session.post(url=url_sign_in, verify=False, data=url_data, headers=headers, timeout=60)
    except:
        output.append(
            f"{ip} - IP does not correspond to a valid VMN, or the VMN isn't currently online. Please try again later.")
        failed_ips.append(ip)
        return
    request_obj_json = request_obj.json()
    if (request_obj_json["status"]["code"] != 200):
        message = request_obj_json["status"]["message"]
        output.append(f"{ip} - {message}")
        failed_ips.append(ip)
        return

    ecp_session = request_obj.cookies['ecp_session']

    cookie = "ecp_session=" + ecp_session
    cookie = unquote(cookie)

    auth = HTTPBasicAuth(user, password)

    referer = "https://" + ip + "/setup/"

    api_headers = {'Content-type': 'application/json', "Referer": referer, "Cookie": cookie}

    # api to get current maintenance mode state

    mm_url = "https://" + ip + "/api/v1/core/platform/maintenanceMode"
    get_mm_request_obj = session.get(url=mm_url, headers=api_headers, auth=auth, verify=False)
    get_mm_request_obj = get_mm_request_obj.json()

    # api to set current maintenance mode state to 'on'

    if (get_mm_request_obj['result']['maintenanceMode'] == 'off'):
        mm_data = {
            "maintenanceMode": "on"
        }
        put_mm_request_obj = session.put(url=mm_url, headers=api_headers, data=json.dumps(mm_data), auth=auth,
                                         verify=False)
        put_mm_request_obj = put_mm_request_obj.json()
    elif (get_mm_request_obj['result']['maintenanceMode'] == 'on'):
        output.append(f"{ip} - Maintenance Mode is already enabled.")
        failed_ips.append(ip)
        return

    # api to check if maintenance mode was set to 'on'

    count = 0
    while (count <= 30):
        count += 1
        try:
            get_mm_request_obj = session.get(url=mm_url, headers=api_headers, auth=auth, verify=False)
        except:
            continue
        get_mm_request_obj = get_mm_request_obj.json()
        if (get_mm_request_obj['result']['maintenanceMode'] == 'on'):
            output.append(f"{ip} - Successfully enabled Maintenance Mode.")
            passed_ips.append(ip)
            return
        elif (get_mm_request_obj['result']['maintenanceMode'] == 'off'):
            mm_data = {
                "maintenanceMode": "on"
            }
            put_mm_request_obj = session.put(url=mm_url, headers=api_headers, data=json.dumps(mm_data), auth=auth,
                                             verify=False)
            put_mm_request_obj = put_mm_request_obj.json()
        else:
            sleep(10)

    # if maintenance mode wasn't set to 'on' in timeout, then exit

    mm_data = {
        "maintenanceMode": "off"
    }
    put_mm_request_obj = session.put(url=mm_url, headers=api_headers, data=json.dumps(mm_data), auth=auth, verify=False)
    put_mm_request_obj = put_mm_request_obj.json()
    output.append(f"{ip} - Could not enable maintenance mode due to active calls or no response from the node. "
                  f"Please try again later.")
    failed_ips.append(ip)
    return


def maintenance_mode_off(*data):
    ip = data[0]
    user = data[1]
    password = data[2]

    session = requests.Session()

    # api to get ecp_session cookie

    url_sign_in = "https://" + ip + "/api/v1/auth/signIn"
    headers = {'Content-type': 'application/json', 'Referer': 'https://web.ciscospark.com'}
    url_data = json.dumps({"password": password, "userName": user})
    try:
        request_obj = session.post(url=url_sign_in, verify=False, data=url_data, headers=headers, timeout=60)
    except:
        output.append(
            f"{ip} - IP does not correspond to a valid VMN, or the VMN isn't currently online. Please try again later.")
        failed_ips.append(ip)
        return
    request_obj_json = request_obj.json()
    if (request_obj_json["status"]["code"] != 200):
        message = request_obj_json["status"]["message"]
        output.append(f"{ip} - {message}")
        failed_ips.append(ip)
        return

    ecp_session = request_obj.cookies['ecp_session']

    cookie = "ecp_session=" + ecp_session
    cookie = unquote(cookie)

    auth = HTTPBasicAuth(user, password)

    referer = "https://" + ip + "/setup/"

    api_headers = {'Content-type': 'application/json', "Referer": referer, "Cookie": cookie}

    # api to get current maintenance mode state

    mm_url = "https://" + ip + "/api/v1/core/platform/maintenanceMode"
    get_mm_request_obj = session.get(url=mm_url, headers=api_headers, auth=auth, verify=False)
    get_mm_request_obj = get_mm_request_obj.json()

    # api to set current maintenance mode state to 'off'

    if (get_mm_request_obj['result']['maintenanceMode'] != 'off'):
        mm_data = {
            "maintenanceMode": "off"
        }
        put_mm_request_obj = session.put(url=mm_url, headers=api_headers, data=json.dumps(mm_data), auth=auth,
                                         verify=False)
        put_mm_request_obj = put_mm_request_obj.json()
        output.append(f"{ip} - Successfully disabled Maintenance Mode.")
        passed_ips.append(ip)
        return
    elif (get_mm_request_obj['result']['maintenanceMode'] == 'off'):
        output.append(f"{ip} - Maintenance Mode is already disabled.")
        failed_ips.append(ip)
        return


if __name__ == "__main__":
    input_file = "input_mm.csv"
    csv_file = open(input_file)
    csv_reader = csv.reader(csv_file)
    cols = next(csv_reader)
    pool = ThreadPool()
    results = {}
    parser = argparse.ArgumentParser(description="Maintenance Mode")
    parser.add_argument('-m', action='store', dest='method', required=True, choices=['on', 'off'], help='Method')
    args = parser.parse_args()
    method = args.method
    if method == 'on':
        print("\n\nEnabling Maintenance Mode. This might take upto 5 minutes. \n")
        results = {data[0]: pool.apply_async(maintenance_mode_on, data) for data in csv_reader if not data[0] == " "}
    else:
        print("\n\nDisabling Maintenance Mode. \n")
        results = {data[0]: pool.apply_async(maintenance_mode_off, data) for data in csv_reader if not data[0] == " "}
    pool.close()
    pool.join()
    for i in output:
        print(i, "\n")

    csv_file.close()

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

import csv
import json
import re
import requests
import subprocess
import warnings
from multiprocessing.pool import ThreadPool
from requests.auth import HTTPBasicAuth
from urllib.parse import unquote
from utils import get_rows, mask_passwords

warnings.filterwarnings("ignore")

output = dict()
regex = r"^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"


def worker(data, columns):
    ip = data[0]
    if ip not in output:
        output[ip] = dict()
    output[ip]["failure"] = []
    output[ip]["success"] = []
    output[ip]["status"] = "PASS"

    num_cols = len(columns)
    num_data = len(data)
    if num_data != num_cols:
        output[ip]["failure"].append(
            f"Wrong number of inputs provided - {num_data}. There should be {num_cols} columns.")
        output[ip]["status"] = "FAIL"
        return

    user = data[1]
    password = data[2]
    new_hostname = data[3]
    new_domain = data[4]
    dns_servers = data[5].split('|')
    ntp_servers = data[6].split('|')
    dns_caching = data[7]
    mtu = data[8]

    for i in range(4 - len(dns_servers)):
        dns_servers.append("")
    dns1 = dns_servers[0]
    dns2 = dns_servers[1]
    dns3 = dns_servers[2]
    dns4 = dns_servers[3]

    for i in range(5 - len(ntp_servers)):
        ntp_servers.append("")
    ntp1 = ntp_servers[0]
    ntp2 = ntp_servers[1]
    ntp3 = ntp_servers[2]
    ntp4 = ntp_servers[3]
    ntp5 = ntp_servers[4]

    if not re.match(regex, ip):
        process = subprocess.Popen(['nslookup', ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if stdout:
            out = stdout.decode("utf-8")
            if re.search(r"Non-authoritative answer", out):
                output[ip]["failure"].append("Invalid Video Mesh Node")
                output[ip]["status"] = "FAIL"
                return
        ret_code = process.returncode
        if ret_code or stderr:
            output[ip]["failure"].append("Invalid Video Mesh Node")
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
        output[ip]["failure"].append("IP/FQDN does not correspond to a valid VMN.")
        output[ip]["status"] = 'FAIL'
        return
    except requests.ConnectionError:
        output[ip]["failure"].append("Connection refused. Please check if the VMN IP/FQDN is correct and up.")
        output[ip]["status"] = 'FAIL'
        return
    except Exception as err:
        output[ip]["failure"].append(f"Error: {err}")
        output[ip]["status"] = 'FAIL'
        return

    try:
        request_obj_json = request_obj.json()
    except Exception as err:
        output[ip]["failure"].append("IP/FQDN does not correspond to a valid VMN.")
        output[ip]["status"] = 'FAIL'
        return

    if request_obj_json["status"]["code"] != 200:
        try:
            message = request_obj_json["result"]["data"]["message"]
        except:
            message = request_obj_json["status"]["message"]
        output[ip]["failure"].append(message)
        output[ip]["status"] = 'FAIL'
        return

    ecp_session = request_obj.cookies['ecp_session']

    cookie = "ecp_session=" + ecp_session
    cookie = unquote(cookie)

    auth = HTTPBasicAuth(user, password)

    referer = "https://" + ip + "/setup/"

    api_headers = {'Content-type': 'application/json', "Referer": referer, "Cookie": cookie}

    # check if maintenance mode is enabled to make network changes

    mm_url = "https://" + ip + "/api/v1/core/platform/maintenanceMode"
    get_mm_request_obj = session.get(url=mm_url, headers=api_headers, auth=auth, verify=False)
    get_mm_request_obj = get_mm_request_obj.json()
    if get_mm_request_obj['result']['maintenanceMode'] != 'on':
        output[ip]["failure"].append(
            "Maintenance Mode is not enabled. Kindly enable Maintenance Mode and try again for this node.")
        output[ip]["status"] = 'FAIL'
        return

    get_network_url = "https://" + ip + "/api/v1/core/platform/network/internal"
    get_request_obj = session.get(url=get_network_url, headers=api_headers, auth=auth, verify=False)
    get_request_obj = get_request_obj.json()
    dhcp = False
    gateway = get_request_obj['result']['data']['gateway']
    ip = get_request_obj['result']['data']['ip']
    mask = get_request_obj['result']['data']['mask']
    dns = get_request_obj['result']['data']['dnsServers']
    dnsCaching = get_request_obj['result']['data']['dnsCaching']
    mtu_get = get_request_obj['result']['data']['mtu']

    get_ntp_url = "https://" + ip + "/api/v1/core/platform/network/ntp"

    ntp_request_obj = session.get(url=get_ntp_url, headers=api_headers, auth=auth, verify=False)
    ntp_request_obj = ntp_request_obj.json()

    ntp = ntp_request_obj['result']['data']

    if new_hostname or new_domain:
        api_flag = True
        get_host_url = "https://" + ip + "/api/v1/core/platform/host"

        host_request_obj = session.get(url=get_host_url, headers=api_headers, auth=auth, verify=False)
        host_request_obj = host_request_obj.json()

        hostname = host_request_obj['result']['data']['hostName']
        domain = host_request_obj['result']['data']['domain']

        if new_hostname == hostname and new_domain == domain:
            output[ip]["failure"].append(
                "*HOSTNAME AND DOMAIN - You have entered the same hostname and domain, as were already existing.")
            output[ip]["status"] = 'FAIL'
            api_flag = False
        if api_flag:
            hostname_api_url = "https://" + ip + "/api/v1/core/platform/host?skipSave=false&skipWarnings=false&skipReboot=true"
            hostname_api_data = {
                "hostName": new_hostname,
                "domain": new_domain
            }
            hostname_api_response = session.put(url=hostname_api_url, data=json.dumps(hostname_api_data),
                                                headers=api_headers, auth=auth, verify=False)
            hostname_api_response = hostname_api_response.json()
            if hostname_api_response["status"]["code"] == 200:
                output[ip]["success"].append("*HOSTNAME AND DOMAIN.")
            else:
                message = hostname_api_response["result"]["data"]["message"]
                output[ip]["failure"].append(f"*HOSTNAME AND DOMAIN - {message}")
                output[ip]["status"] = 'FAIL'

    if dns1 or dns2 or dns3 or dns4:
        api_flag = True
        existing_dns = dns
        dns = []
        if dns1:
            dns.append(dns1)
        if dns2:
            dns.append(dns2)
        if dns3:
            dns.append(dns3)
        if dns4:
            dns.append(dns4)
        if sorted(dns) == sorted(existing_dns):
            output[ip]["failure"].append("*DNS - You have entered the Same DNS servers, as were already existing.")
            output[ip]["status"] = 'FAIL'
            api_flag = False
        if api_flag:
            internal_api_url = "https://" + ip + "/api/v1/core/platform/network/internal?skipSave=false&skipWarnings=false&skipReboot=true"
            internal_api_data = {
                "dhcp": dhcp,
                "ip": ip,
                "mask": mask,
                "gateway": gateway,
                "dnsServers": dns
            }
            internal_api_response = session.put(url=internal_api_url, data=json.dumps(internal_api_data),
                                                headers=api_headers, auth=auth, verify=False)
            internal_api_response = internal_api_response.json()
            if (internal_api_response["status"]["code"] == 200):
                output[ip]["success"].append("*DNS.")
            else:
                message = internal_api_response["result"]["data"][0]["message"]
                output[ip]["failure"].append(
                    f"*DNS - {message} - None of the DNS servers were updated. Kindly input correct DNS server and try again.")
                output[ip]["status"] = 'FAIL'

    if ntp1 or ntp2 or ntp3 or ntp4 or ntp5:
        api_flag = True
        existing_ntp = ntp
        ntp = []
        if ntp1:
            ntp.append(ntp1)
        if ntp2:
            ntp.append(ntp2)
        if ntp3:
            ntp.append(ntp3)
        if ntp4:
            ntp.append(ntp4)
        if ntp5:
            ntp.append(ntp5)
        if sorted(ntp) == sorted(existing_ntp):
            output[ip]["failure"].append("*NTP - You have entered the Same NTP servers, as were already existing.")
            output[ip]["status"] = 'FAIL'
            api_flag = False
        if api_flag:
            ntp_api_url = "https://" + ip + "/api/v1/core/platform/network/ntp?skipSave=false&skipWarnings=false&skipReboot=true"
            ntp_api_data = {
                "ntpServers": ntp
            }
            ntp_api_response = session.put(url=ntp_api_url, data=json.dumps(ntp_api_data), headers=api_headers,
                                           auth=auth, verify=False)
            ntp_api_response = ntp_api_response.json()
            if (ntp_api_response["status"]["code"] == 200):
                output[ip]["success"].append("*NTP.")
            else:
                message = ntp_api_response["result"]["data"][0]["message"]
                output[ip]["failure"].append(
                    f"*NTP - {message} - None of the NTP servers were updated. Kindly input correct NTP server and try again.")
                output[ip]["status"] = 'FAIL'

    if mtu:
        api_flag = True
        if not mtu.isdigit():
            output[ip]["failure"].append(f"*MTU - Please enter a valid positive digit.")
            output[ip]["status"] = "FAIL"
            api_flag = False
        if int(mtu) == mtu_get:
            output[ip]["failure"].append(f"*MTU - MTU is already set to {mtu}.")
            output[ip]["status"] = 'FAIL'
            api_flag = False
        if api_flag:
            mtu_api_url = "https://" + ip + "/api/v1/core/platform/network/mtu"
            mtu_api_data = {
                "internalInterfaceMtu": int(mtu)
            }
            mtu_api_response = session.put(url=mtu_api_url, data=json.dumps(mtu_api_data), headers=api_headers,
                                           auth=auth, verify=False)
            mtu_api_response = mtu_api_response.json()
            if mtu_api_response["status"]["code"] == 200:
                output[ip]["success"].append("*MTU.")
            else:
                message = mtu_api_response["result"]["data"]["message"]
                output[ip]["failure"].append(f"*MTU - {message}")
                output[ip]["status"] = 'FAIL'

    if dns_caching:
        api_flag = True
        if dns_caching == "True" or dns_caching == "true":
            dns_caching_flag = True
        elif dns_caching == "False" or dns_caching == "false":
            dns_caching_flag = False
        else:
            output[ip]["failure"].append(f"*DNS CACHING - Kindly enter true or false.")
            output[ip]["status"] = 'FAIL'
            api_flag = False
        if dnsCaching == dns_caching_flag:
            output[ip]["failure"].append(f"*DNS CACHING - DNS Caching is already set to {dns_caching}.")
            output[ip]["status"] = 'FAIL'
            api_flag = False
        if api_flag:
            dns_caching_api_url = "https://" + ip + "/api/v1/core/platform/network/dnsCaching"
            dns_caching_api_data = {
                "dnsCaching": dns_caching_flag
            }
            dns_caching_api_response = session.put(url=dns_caching_api_url, data=json.dumps(dns_caching_api_data),
                                                   headers=api_headers, auth=auth, verify=False)
            dns_caching_api_response = dns_caching_api_response.json()
            if dns_caching_api_response["status"]["code"] == 200:
                output[ip]["success"].append("*DNS CACHING.")
            else:
                message = dns_caching_api_response["result"]["data"]["message"]
                output[ip]["failure"].append(f"*DNS CACHING - {message}")
                output[ip]["status"] = 'FAIL'


if __name__ == "__main__":
    input_file = "input_network.csv"
    csv_file = open(input_file)
    csv_reader = csv.reader(csv_file)
    cols = next(csv_reader)
    pool = ThreadPool()
    results = {data[0]: pool.apply_async(worker, args=(data, cols)) for data in csv_reader if
               data and not data[0] == " "}
    pool.close()
    pool.join()
    for i in output:
        print(f"\nvideo_mesh_node : {i}\n")
        if output[i]["failure"]:
            print("\tFailures : \n")
            for j in output[i]["failure"]:
                print("\t\t", j, "\n")
        if output[i]["success"]:
            print("\n\tSuccess : \n")
            for j in output[i]["success"]:
                print("\t\t", j, "\n")
            print(f"\n\tNOTE: The node {i} is rebooting after applying the changes. "
                  f"Please wait for a minute before you try to login to the node.\n")
        print("--------------------------------------------------------------------------------------------------\n")

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

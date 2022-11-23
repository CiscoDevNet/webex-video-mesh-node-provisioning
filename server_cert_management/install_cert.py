import argparse
import csv
import json
import os
import requests
import warnings
from multiprocessing.pool import ThreadPool
from requests.auth import HTTPBasicAuth
from utils_cert import get_cookie, check_node, get_file_contents, get_modified_time, validate_install_input
import sys
sys.path.append('..')
from utils import get_rows, mask_passwords


warnings.filterwarnings("ignore")
output = dict()


def get_ca_cert_key(ip, session, api_headers, auth):
    csr_url = f"https://{ip}/api/v1/certManager/caCert"
    csr_api_response = session.get(url=csr_url, headers=api_headers, auth=auth, verify=False)
    csr_api_response = csr_api_response.json()
    if csr_api_response.get('result', None).get('caCert', None):
        return True, csr_api_response.get('result', None).get('caCert', None).get('fileName', None)
    else:
        return False, None


def upload_ca_cert(ip, source, file_name, session, api_headers, auth):
    cert_url = f"https://{ip}/api/v1/certManager/caCert/cert"
    file_path = f"{source}/{file_name}"
    if not os.path.exists(file_path):
        message = f"The CA certificate '{file_path}' does not exist. " \
                  f"Check if '{source}' folder exists and '{file_name}' is present under '{source}/'"
        output[ip]["failure"].append(message)
        output[ip]["status"] = "FAIL"
        return
    ca_cert = get_file_contents(file_path)
    modified_time = get_modified_time(file_path)
    file_size = os.path.getsize(file_path)
    cert_api_data = {
        "fileName": file_path,
        "lastModified": modified_time,
        "size": file_size,
        "type": "application/pkcs8",
        "cert": ca_cert
    }
    csr_api_response = session.post(url=cert_url, data=json.dumps(cert_api_data),
                                    headers=api_headers, auth=auth, verify=False)
    csr_api_response = csr_api_response.json()
    if csr_api_response['status']['code'] == 200:
        message = "Successfully uploaded the certificate"
        output[ip]["success"].append(message)
    else:
        message = csr_api_response['status']['message']
        output[ip]["failure"].append(message)
        output[ip]["status"] = "FAIL"
        return


def upload_key(ip, source, file_name, session, api_headers, auth, passphrase):
    key_url = f"https://{ip}/api/v1/certManager/caCert/key"
    file_path = f"{source}/{file_name}"
    if not os.path.exists(file_path):
        message = f"The private key '{file_path}' does not exist. " \
                  f"Check if '{source}' folder exists and '{file_name}' is present under '{source}'/"
        output[ip]["failure"].append(message)
        output[ip]["status"] = "FAIL"
        return
    ca_key = get_file_contents(file_path)
    modified_time = get_modified_time(file_path)
    file_size = os.path.getsize(file_path)
    key_api_data = {
        "caKey": ca_key,
        "fileName": file_path,
        "lastModified": modified_time,
        "size": file_size,
        "passphrase": passphrase,
        "type": "application/pkcs8"
    }
    csr_api_response = session.post(url=key_url, data=json.dumps(key_api_data),
                                    headers=api_headers, auth=auth, verify=False)
    csr_api_response = csr_api_response.json()
    if csr_api_response['status']['code'] == 200:
        message = "Successfully uploaded the key"
        output[ip]["success"].append(message)
    else:
        message = csr_api_response['status']['message']
        output[ip]["failure"].append(message)
        output[ip]["status"] = "FAIL"
        return


def get_installation_status(ip, session, api_headers, auth):
    csr_url = f"https://{ip}/api/v1/certManager/caCert"
    csr_api_response = session.get(url=csr_url, headers=api_headers, auth=auth, verify=False)
    csr_api_response = csr_api_response.json()
    is_installed = csr_api_response['result'].get('caCertsInstalled', False)
    is_pending = csr_api_response['result'].get('certInstallRequestPending', False)

    if csr_api_response['result'].get('caCert', None):
        is_cert_uploaded = True
    else:
        is_cert_uploaded = False

    if csr_api_response['result'].get('caKey', None):
        is_key_uploaded = True
    else:
        is_key_uploaded = False

    return is_installed, is_pending, is_cert_uploaded, is_key_uploaded


def install(ip, session, api_headers, auth):
    installed, pending, cert_uploaded, key_uploaded = get_installation_status(ip, session, api_headers, auth)

    if not cert_uploaded:
        message = "CA Certificate is not uploaded. Please upload CA certificate to install."
        output[ip]["failure"].append(message)
        output[ip]["status"] = "FAIL"
        return

    if not key_uploaded:
        message = "Private key is not uploaded. Please upload the key to install."
        output[ip]["failure"].append(message)
        output[ip]["status"] = "FAIL"
        return

    if pending:
        message = "Certificate and private key PENDING installation. It might take a few seconds to reflect." \
                  "If the node is in maintenance mode, it will get installed once it is disabled."

        output[ip]["success"].append(message)
        return

    if installed:
        message = "Certificate and private key already installed. Please re-upload to re-install."
        output[ip]["failure"].append(message)
        output[ip]["status"] = "FAIL"
        return

    cert_url = f"https://{ip}/api/v1/certManager/caCert/install"
    csr_api_response = session.post(url=cert_url, headers=api_headers, auth=auth, verify=False)
    csr_api_response = csr_api_response.json()
    if csr_api_response['status']['code'] == 200:
        if csr_api_response['result'].get('caCertsInstalled', False) or \
                csr_api_response['result'].get('certInstallCompleted', False):
            message = "Successfully installed certificate and key. It might take a few seconds to reflect."
            output[ip]["success"].append(message)
        elif csr_api_response['result'].get('certInstallRequestPending', False):
            message = "Certificate and private key PENDING installation. It might take a few seconds to reflect. " \
                      "If the node is in maintenance mode, it will get installed once it is disabled."
            output[ip]["success"].append(message)
        else:
            message = csr_api_response['status']['message']
            if not message:
                message = "Cert and key could not be installed"
            output[ip]["failure"].append(message)
            output[ip]["status"] = "FAIL"
            return
    else:
        message = csr_api_response['status']['message']
        if not message:
            message = "Failed to install certificate and key"
        output[ip]["failure"].append(message)
        output[ip]["status"] = "FAIL"
        return


def download_ca_cert(ip, session, api_headers, auth):
    status, file_name = get_ca_cert_key(ip, session, api_headers, auth)
    if not status:
        message = "CA Certificate couldn't be downloaded: Does not exist."
        output[ip]["failure"].append(message)
        output[ip]["status"] = "FAIL"
        return

    if file_name:
        file_name = file_name.split('/')[-1]
        csr_url = f"https://{ip}/api/v1/certManager/caCert/cert"
        csr_api_response = session.get(url=csr_url, headers=api_headers, auth=auth, verify=False)
        if csr_api_response.status_code == 200:
            try:
                if not os.path.exists(ip):
                    os.mkdir(ip)
                with open(f"{ip}/{file_name}", "wt") as fh:
                    fh.write(csr_api_response.text)
            except Exception as err:
                output[ip]["failure"].append(str(err))
                output[ip]["status"] = 'FAIL'
            else:
                message = "CA Certificate downloaded"
                output[ip]["success"].append(message)
        else:
            output[ip]["failure"].append("Error downloading CA certificate.")
            output[ip]["status"] = 'FAIL'


def delete_ca_cert(ip, session, api_headers, auth):
    status = get_ca_cert_key(ip, session, api_headers, auth)
    if not status[0]:
        message = "Couldn't delete CA certificate: Does not exist."
        output[ip]["failure"].append(message)
        output[ip]["status"] = "FAIL"
        return

    cert_url = f"https://{ip}/api/v1/certManager/caCert/cert"
    csr_api_response = session.delete(url=cert_url, headers=api_headers, auth=auth, verify=False)
    csr_api_response = csr_api_response.json()
    message = csr_api_response['status']['message']
    if csr_api_response['status']['code'] == 200:
        if not message:
            message = "Successfully deleted CA certificate"
        output[ip]["success"].append(message)
    else:
        if not message:
            message = "Error deleting the CA certificate"
        output[ip]["failure"].append(message)
        output[ip]["status"] = "FAIL"


def worker(data, columns, option):
    ip = data[0]
    user = data[1]
    password = data[2]
    source = data[3]
    cert = data[4]
    passphrase = data[5]
    key = data[6]

    if ip not in output:
        output[ip] = dict()
    output[ip]["failure"] = []
    output[ip]["success"] = []
    output[ip]["status"] = "PASS"

    validation_status = validate_install_input(data, columns, option)
    if not validation_status[0]:
        output[ip]["failure"].append(validation_status[1])
        output[ip]["status"] = 'FAIL'
        return

    node_status = check_node(ip)
    if not node_status[0]:
        output[ip]["failure"].append(node_status[1])
        output[ip]["status"] = 'FAIL'
        return

    session = requests.Session()
    result = get_cookie(session, ip, user, password)
    if result[0]:
        cookie = result[1]
    else:
        output[ip]["failure"].append(result[1])
        output[ip]["status"] = 'FAIL'
        return

    auth = HTTPBasicAuth(user, password)
    referer = f"https://{ip}/setup/"
    api_headers = {'Content-type': 'application/json', "Referer": referer, "Cookie": cookie}

    try:
        print()
        if option == 'uploadCert':
            print(f"{ip}: Uploading CA cert")
            upload_ca_cert(ip, source, cert, session, api_headers, auth)
        elif option == 'uploadKey':
            print(f"{ip}: Uploading private key")
            upload_key(ip, source, key, session, api_headers, auth, passphrase)
        elif option == 'install':
            print(f"{ip}: Installing CA cert and private key")
            install(ip, session, api_headers, auth)
        elif option == 'deleteCertCA':
            print(f"{ip}: Deleting CA certificate")
            delete_ca_cert(ip, session, api_headers, auth)
        elif option == 'downloadCertCA':
            print(f"{ip}: Downloading CA certificate")
            download_ca_cert(ip, session, api_headers, auth)
        else:
            print(f"{ip}: Wrong option passed!!")
    except Exception as err:
        return f"{ip}: Some error occurred: {err}"


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="CA Certificate Installation")
    option_choices = ['uploadCert', 'uploadKey', 'install', 'downloadCertCA', 'deleteCertCA']
    parser.add_argument('--action', action='store', required=True, choices=option_choices, help='Action to perform')
    args = parser.parse_args()
    action = args.action

    input_file = "input_install.csv"
    csv_file = open(input_file)
    csv_reader = csv.reader(csv_file)
    cols = next(csv_reader)
    pool = ThreadPool()
    results = {data[0]: pool.apply_async(worker, args=(data, cols, action))
               for data in csv_reader if data and not data[0] == " "}
    pool.close()
    pool.join()

    print()
    print("---------Status---------")
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
    print("------------------------")
    print()

    failed_ips = list()
    passed_ips = list()
    for ip in output:
        if output[ip]['status'] == 'FAIL':
            failed_ips.append(ip)
        else:
            passed_ips.append(ip)

    rows_status = get_rows(input_file, passed_ips, failed_ips, 0)
    if rows_status:
        ret = mask_passwords(input_file, rows_status[0], rows_status[1], col_num=[2, 5])
        if ret:
            print("\n Successfully masked the passwords")
        else:
            print("\n Could not mask the passwords")
    else:
        print("\n Could not mask the passwords")

    print('\n')


import argparse
import csv
import json
import os
import requests
import warnings
from multiprocessing.pool import ThreadPool
from requests.auth import HTTPBasicAuth
from utils_cert import get_cookie, check_node, validate_generate_input
import sys
sys.path.append('..')
from utils import get_rows, mask_passwords


warnings.filterwarnings("ignore")
output = dict()
regex = r"^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"


def get_cert_key(ip, session, api_headers, auth, cert_type):
    if cert_type not in ['csr', 'caKey']:
        return False

    csr_url = f"https://{ip}/api/v1/certManager/caCert"
    csr_api_response = session.get(url=csr_url, headers=api_headers, auth=auth, verify=False)
    csr_api_response = csr_api_response.json()
    if csr_api_response.get('result', None).get(cert_type, None):
        return True
    else:
        return False


def generate_csr(csr_data, session, api_headers, auth):
    ip = csr_data[0]
    is_cert_present = get_cert_key(ip, session, api_headers, auth, cert_type='csr')
    is_key_present = get_cert_key(ip, session, api_headers, auth, cert_type='caKey')

    if is_cert_present and is_key_present:
        message = "Certificate and Private Key already exists. Please ensure any existing certificate and " \
                  "private key are deleted before generating a CSR."
        output[ip]["failure"].append(message)
        output[ip]["status"] = "FAIL"
        return
    elif is_cert_present:
        message = "Certificate already exists. Please ensure existing certificate is deleted before generating a CSR."
        output[ip]["failure"].append(message)
        output[ip]["status"] = "FAIL"
        return
    elif is_key_present:
        message = "Private Key already exists. Please ensure existing private key is deleted before generating a CSR."
        output[ip]["failure"].append(message)
        output[ip]["status"] = "FAIL"
        return

    name = csr_data[3]
    email = csr_data[4]
    san = csr_data[5]
    san = ','.join(san.split('|'))
    org = csr_data[6]
    org_unit = csr_data[7]
    city = csr_data[8]
    state = csr_data[9]
    country = csr_data[10]
    passphrase = csr_data[11]
    bit_size = csr_data[12]
    if bit_size:
        bit_size = int(bit_size)

    csr_url = f"https://{ip}/api/v1/certManager/caCert/csr"
    csr_api_data = {"csrInfo": {
        "commonName": name,
        "emailAddress": email,
        "altNames": san,
        "organization": org,
        "organizationUnit": org_unit,
        "locality": city,
        "state": state,
        "country": country,
        "passphrase": passphrase,
        "keyBitsize": bit_size
        }
    }
    csr_api_response = session.post(url=csr_url, data=json.dumps(csr_api_data),
                                    headers=api_headers, auth=auth, verify=False)
    csr_api_response = csr_api_response.json()
    message = csr_api_response['status']['message']
    if not message:
        message = "Successfully generated certificate and private key"

    if csr_api_response['status']['code'] == 200:
        output[ip]["success"].append(message)
        download_cert(ip, session, api_headers, auth)
        download_key(ip, session, api_headers, auth)
    else:
        output[ip]["failure"].append(message)
        output[ip]["status"] = 'FAIL'


def download_cert(ip, session, api_headers, auth):
    if not get_cert_key(ip, session, api_headers, auth, cert_type='csr'):
        message = "Certificate didn't download: Does not exist."
        output[ip]["failure"].append(message)
        output[ip]["status"] = "FAIL"
        return

    csr_url = f"https://{ip}/api/v1/certManager/caCert/csr"
    csr_api_response = session.get(url=csr_url, headers=api_headers, auth=auth, verify=False)
    if csr_api_response.status_code == 200:
        try:
            if not os.path.exists(ip):
                os.mkdir(ip)
            with open(f"{ip}/videoMeshCsr.csr", "wt") as fh:
                fh.write(csr_api_response.text)
        except Exception as err:
            output[ip]["failure"].append(str(err))
            output[ip]["status"] = 'FAIL'
        else:
            message = "Certificate downloaded"
            output[ip]["success"].append(message)
    else:
        output[ip]["failure"].append("Error downloading certificate.")
        output[ip]["status"] = 'FAIL'


def download_key(ip, session, api_headers, auth):
    if not get_cert_key(ip, session, api_headers, auth, cert_type='caKey'):
        message = "Private key didn't download: Does not exist."
        output[ip]["failure"].append(message)
        output[ip]["status"] = "FAIL"
        return

    csr_url = f"https://{ip}/api/v1/certManager/caCert/key"
    csr_api_response = session.get(url=csr_url, headers=api_headers, auth=auth, verify=False)
    if csr_api_response.status_code == 200:
        try:
            if not os.path.exists(ip):
                os.mkdir(ip)
            with open(f"{ip}/VideoMeshGeneratedPrivate.key", "wt") as fh:
                fh.write(csr_api_response.text)
        except Exception as err:
            output[ip]["failure"].append(str(err))
            output[ip]["status"] = 'FAIL'
        else:
            message = "Private key downloaded"
            output[ip]["success"].append(message)


def delete_cert(ip, session, api_headers, auth):
    if not get_cert_key(ip, session, api_headers, auth, cert_type='csr'):
        message = "Couldn't delete certificate: Does not exist."
        output[ip]["failure"].append(message)
        output[ip]["status"] = "FAIL"
        return

    csr_url = f"https://{ip}/api/v1/certManager/caCert/csr"
    csr_api_response = session.delete(url=csr_url, headers=api_headers, auth=auth, verify=False)
    csr_api_response = csr_api_response.json()

    message = csr_api_response['status']['message']
    if csr_api_response['status']['code'] == 200:
        if not message:
            message = "Successfully deleted the certificate from the node."
        output[ip]["success"].append(message)
    else:
        if not message:
            message = "Error deleting the certificate!"
        output[ip]["failure"].append(message)
        output[ip]["status"] = "FAIL"


def delete_key(ip, session, api_headers, auth):
    if not get_cert_key(ip, session, api_headers, auth, cert_type='caKey'):
        message = "Couldn't delete private key: Does not exist."
        output[ip]["failure"].append(message)
        output[ip]["status"] = "FAIL"
        return

    csr_url = f"https://{ip}/api/v1/certManager/caCert/key"
    csr_api_response = session.delete(url=csr_url, headers=api_headers, auth=auth, verify=False)
    csr_api_response = csr_api_response.json()

    message = csr_api_response['status']['message']
    if csr_api_response['status']['code'] == 200:
        if not message:
            message = "Successfully deleted the private key from the node."
        output[ip]["success"].append(message)
    else:
        if not message:
            message = "Error deleting the private key!"
        output[ip]["failure"].append(message)
        output[ip]["status"] = "FAIL"


def worker(data, columns, option):
    ip = data[0]
    user = data[1]
    password = data[2]

    if ip not in output:
        output[ip] = dict()
    output[ip]["failure"] = []
    output[ip]["success"] = []
    output[ip]["status"] = "PASS"

    validation_status = validate_generate_input(data, columns, option)
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
        if option == 'generate':
            print(f"{ip}: Generating CSR and private key")
            generate_csr(data, session, api_headers, auth)
        elif option == 'downloadCert':
            print(f"{ip}: Downloading certificate")
            download_cert(ip, session, api_headers, auth)
        elif option == 'downloadKey':
            print(f"{ip}: Downloading private key")
            download_key(ip, session, api_headers, auth)
        elif option == 'deleteCert':
            print(f"{ip}: Deleting certificate")
            delete_cert(ip, session, api_headers, auth)
        elif option == 'deleteKey':
            print(f"{ip}: Deleting private key")
            delete_key(ip, session, api_headers, auth)
        else:
            print(f"{ip}: Wrong option passed!!")
    except Exception as err:
        return f"{ip}: Some error occurred: {err}"


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="CSR creation")
    option_choices = ['generate', 'downloadCert', 'downloadKey', 'deleteCert', 'deleteKey']
    parser.add_argument('--action', action='store', required=True, choices=option_choices, help='Action to perform')
    args = parser.parse_args()
    action = args.action

    input_file = "input_generate.csv"
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
        ret_cred = mask_passwords(input_file, rows_status[0], rows_status[1], col_num=[2, 11])
        if ret_cred:
            print("\n Successfully masked the passwords")
        else:
            print("\n Could not mask the passwords")
    else:
        print("\n Could not mask the passwords")

    print('\n')

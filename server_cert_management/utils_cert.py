import os
import re
import json
import requests
import subprocess
from urllib.parse import unquote

regex = r"^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"


def get_cookie(session, ip, user, password):
    # api to get ecp_session cookie
    url_sign_in = "https://" + ip + "/api/v1/auth/signIn"
    headers = {'Content-type': 'application/json', 'Referer': 'https://web.ciscospark.com'}
    url_data = json.dumps({"password": password, "userName": user})
    try:
        request_obj = session.post(url=url_sign_in, verify=False, data=url_data, headers=headers, timeout=60)
    except requests.ConnectTimeout:
        return False, f"IP/FQDN does not correspond to a valid VMN."
    except requests.ConnectionError:
        return False, "Connection refused. Please check it is a valid VMN. If yes, validate if it is up."

    request_obj_json = request_obj.json()
    if request_obj_json["status"]["code"] != 200:
        try:
            message = request_obj_json["result"]["data"]["message"]
        except:
            message = request_obj_json["status"]["message"]

        return False, message

    ecp_session = request_obj.cookies['ecp_session']
    cookie = "ecp_session=" + ecp_session
    cookie = unquote(cookie)
    return True, cookie


def check_node(ip):
    is_valid = (True, "Pass")
    nslookup_err_pattern = r"server can't find"
    if not re.match(regex, ip):
        process = subprocess.Popen(['nslookup', ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        ret_code = process.returncode
        if (ret_code or stderr) or (stdout and re.search(nslookup_err_pattern, stdout.decode("utf-8"))):
            is_valid = (False, "Invalid Video Mesh Node")
    return is_valid


def get_modified_time(file_name):
    m_time = 0
    try:
        m_time = os.path.getmtime(file_name)
    except Exception as err:
        print(f"ERROR: {str(err)}")
    return m_time


def get_file_contents(file_name):
    try:
        with open(file_name, 'rt') as fh:
            key = fh.read()
    except Exception as err:
        print(f"ERROR: {str(err)}")

    return key


def validate_generate_input(data, columns, option):
    validation_result = (True, "Pass")
    num_cols = len(columns)
    num_data = len(data)
    if num_data != num_cols:
        return False, f"Wrong number of inputs provided - {num_data}. There should be {num_cols} columns."

    if option == 'generate':
        generate_validations = list()
        common_name = data[3]
        if not common_name:
            generate_validations.append(f"Common name is mandatory for generating CSR. It is missing.")

        passphrase = data[11]
        if passphrase and len(passphrase) < 4:
            generate_validations.append(f"Passphrase should be 4 or more characters.")

        key_bit_size = data[12]
        valid_sizes = ['2048', '4096']
        if key_bit_size and key_bit_size not in valid_sizes:
            generate_validations.append(f"Key Bit Size should be either {' or '.join(valid_sizes)}. "
                                        f"You have entered {key_bit_size}.")
        if generate_validations:
            ret_msg = '\n'.join(generate_validations)
            validation_result = (False, ret_msg)

    return validation_result


def validate_install_input(data, columns, option):
    validation_result = (True, "Pass")
    print("Validating install inputs..")
    num_cols = len(columns)
    num_data = len(data)
    if num_data != num_cols:
        return False, f"Wrong number of inputs provided - {num_data}. There should be {num_cols} columns."

    ip = data[0]
    user = data[1]
    password = data[2]
    source = data[3]
    cert = data[4]
    passphrase = data[5]
    key = data[6]

    missing_fields = list()
    if not ip:
        missing_fields.append('FQDN/IP')
    if not user:
        missing_fields.append('Username')

    if not password:
        missing_fields.append('Password')

    if option == 'uploadCert' or option == 'uploadKey':
        if not source:
            missing_fields.append('Source directory')

    if option == 'uploadCert' and not cert:
        missing_fields.append('CA certificate')

    if option == 'uploadKey' and not key:
        missing_fields.append('Private key')

    if missing_fields:
        validation_result = (False, f"Following field(s) is/are missing:\n{', '.join(missing_fields)}\n")

    return validation_result

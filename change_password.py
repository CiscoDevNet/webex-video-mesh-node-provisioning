import csv
import requests
import json
import re
from multiprocessing.pool import ThreadPool
import warnings
import subprocess
from utils import mask_passwords

warnings.filterwarnings("ignore")

errors = []
success = []
failed_rows = []
passed_rows = []
regex = r"^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"


def worker(*data, row=None):
    ip = data[0]
    if data[1]:
        old_password = data[1]
    else:
        old_password = "cisco"
    password = data[2]
    if not re.match(regex, ip):
        process = subprocess.Popen(['nslookup', ip], stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        ret_code = process.returncode
        if ret_code:
            errors.append(f"{ip} - IP does not correspond to a valid VMN.")
            failed_rows.append(row)
            return
    url = "https://" + ip + "/api/v1/auth/users/password"
    referer = "https://" + ip + "/setup/"
    headers = {"Referer": referer, "Content-Type": "application/json", "Accept": "*/*"}
    data = {
        "userName": "admin",
        "currentPassword": old_password,
        "newPassword": password
    }
    try:
        response = requests.put(url, data=json.dumps(data), headers=headers, verify=False, timeout=60)
    except(requests.ConnectTimeout):
        errors.append(f"{ip} - IP does not correspond to a valid VMN.")
        failed_rows.append(row)
        return
    except(requests.ConnectionError):
        errors.append(f"{ip} - Connection refused.")
        failed_rows.append(row)
        return
    try:
        res = response.json()
    except:
        print("Error for ", ip, ": ", res)
    if (res["status"]["code"] == 200):
        success.append(ip)
        passed_rows.append(row)
        return
    else:
        message = res["result"]["data"]["message"]
        errors.append(f"{ip} - {message}")
        failed_rows.append(row)
        return


if __name__ == "__main__":
    print("\nPassword change in progress. This might take upto 2 minutes....\n")
    input_file = "input_password.csv"
    csv_file = open(input_file)
    csv_reader = csv.reader(csv_file)
    cols = next(csv_reader)
    pool = ThreadPool()
    results = {}
    results = {data[0]: pool.apply_async(worker, args=data, kwds={'row': row_num}) for row_num, data in enumerate(csv_reader)}
    pool.close()
    pool.join()
    if errors:
        print("\nPassword could not be changed for the following IPs:\n")
        for i in errors:
            print(i, "\n")
    print("\n")
    if success:
        print("\nPassword changed successfully for the following IPs:\n")
        for i in success:
            print(i, "\n")

    csv_file.close()

    ret = mask_passwords(input_file, passed_rows, failed_rows, col_num=[1, 2])
    if ret:
        print("\n Successfully masked the passwords")
    else:
        print("\n Could not mask the passwords")

    print("\n")


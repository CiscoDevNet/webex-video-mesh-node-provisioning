import csv
import time
import re
import json
import subprocess
import multiprocessing as mp
from os import path
from time import sleep
from driver_guest_info import worker
from deployment_progress import progress
from host_validation import host_validation
from utils import get_rows
from utils import mask_passwords


def validation_check():
    print("\nPerforming validations on the input file.....")
    host_validation()

    with open('config.json', 'r') as fh:
        config_details = json.load(fh)

    ovf_filename = config_details['ovf_filename']
    regex = r"^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
    # regex = r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}"
    hostname_regex = r"(?!-)[.A-Z\d-]{1,63}(?<!-)$"
    csv_file = open("input_data.csv")
    csv_reader = csv.reader(csv_file)
    cols = next(csv_reader)
    vm_names = list()
    ips = list()
    not_deployed = {}
    flag = False
    print("Checking for invalid input in other fields\n")
    if not path.exists(ovf_filename):
        print(f'OVF file "{ovf_filename}" does not exist in the current directory. Please place it and re-run.\n')
        exit(1)
    for i, row in enumerate(csv_reader):
        error = []
        if not re.match(regex, row[0]):
            error.append("ESXi Host IP")
            flag = True
        if not re.match(regex, row[5]):
            error.append("Invalid/blank IP")
            flag = True
        if not re.match(regex, row[6]):
            error.append("Netmask")
            flag = True
        if not re.match(regex, row[7]):
            error.append("Gateway")
            flag = True

        # DNS validation
        dns_servers = row[8].split('|')
        dns_flag = False
        if len(dns_servers) > 4:
            error.append("DNS should not be more than 4")
            flag = True
        else:
            for dns in dns_servers:
                if not re.match(regex, dns):
                    error.append("DNS")
                    flag = True
                else:
                    if not re.match(regex, dns):
                        process = subprocess.Popen(['nslookup', dns], stdout=subprocess.PIPE,
                                                   stderr=subprocess.PIPE)
                        stdout, stderr = process.communicate()
                        ret_code = process.returncode
                        if ret_code:
                            error.append(f"Unable to query DNS '{dns}'")
                            dns_flag = True
                            flag = True

        # Hostname validation
        if '.' in row[10] and not dns_flag:
            host_name_valid = False
            for dns in dns_servers:
                process = subprocess.Popen(['nslookup', row[10], dns], stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()
                ret_code = process.returncode
                if not ret_code:
                    host_name_valid = True
                    break
            if not host_name_valid:
                error.append(f"Unable to resolve FQDN '{row[10]}' against the DNS servers")
                flag = True
        else:
            if not re.match(hostname_regex, row[10], re.IGNORECASE):
                error.append("Hostname")
                flag = True

        if not (row[13] == "VMNLite" or row[13] == "CMS1000"):
            error.append("Deployment Type")
            flag = True
        if not row[4]:
            error.append("Blank VM Name")
            flag = True
        if not re.match(hostname_regex, row[10], re.IGNORECASE):
            error.append("Hostname")
            flag = True

        # Checking for duplicate VM names
        if row[4] in vm_names:
            error.append("Duplicate VM Name")
            flag = True
        vm_names.append(row[4])

        # Checking for duplicate IP Addresses
        if row[5] in ips:
            error.append("Duplicate IP")
            flag = True
        ips.append(row[5])

        # NTP server validation
        ntp_servers = row[9].split('|')
        if len(ntp_servers) > 5:
            error.append("NTP should not be more than 5")
            flag = True
        else:
            for ntp in ntp_servers:
                if not re.match(regex, ntp):
                    process = subprocess.Popen(['nslookup', ntp], stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE)
                    stdout, stderr = process.communicate()
                    ret_code = process.returncode
                    if ret_code:
                        error.append(f"Unable to query NTP '{ntp}'")
                        flag = True

        if flag:
            not_deployed[i + 1] = error

    csv_file.close()
    if flag:
        print("\nRow number(s) in csv with incorrect/invalid input format: \n")
        # print(json.dumps(not_deployed, indent=6))
        for i in not_deployed:
            if not_deployed[i]:
                print(i, ":", not_deployed[i], "\n")
        print("\n\nPlease validate and re-run the script after correcting them.")
        print("Exiting...\n\n")
        exit()


if __name__ == "__main__":
    start_time = time.time()
    validation_check()  # Performing input validation checks
    file_name = "input_data.csv"
    csv_file = open(file_name)
    csv_reader = csv.reader(csv_file)
    cols = next(csv_reader)
    results = {}

    pool = mp.Pool(processes=(mp.cpu_count() - 1))
    results = {row[5]: pool.apply_async(worker, row) for row in csv_reader}
    passed, failed = progress(results)

    csv_file.close()
    end_time = time.time()
    print("\n****** TIME TAKEN FOR DEPLOYING THE VMNs {:0.2f} MINUTES ******\n".format((end_time - start_time) / 60))

    rows_status = get_rows(file_name, passed, failed, 5)
    if rows_status:
        ret = mask_passwords(file_name, rows_status[0], rows_status[1], col_num=2)
        if ret:
            print("\n Successfully masked the passwords")
        else:
            print("\n Could not mask the passwords")
    else:
        print("\n Could not mask the passwords")

    print("\n")

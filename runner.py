import csv
from textwrap import indent
import time
import multiprocessing as mp
import re
import json
from driver_guest_info import worker
from deployment_progress import progress


def validation_check():
    # regex = r"^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
    regex = r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}"
    hostname_regex = r"(?!-)[A-Z\d-]{1,63}(?<!-)$"
    csv_file = open("input_data.csv")
    csv_reader = csv.reader(csv_file)
    cols = next(csv_reader)
    vm_names = list()
    ips = list()
    not_deployed = {}
    flag = False

    for i, row in enumerate(csv_reader):
        error = []
        if not re.search(regex, row[0]):
            error.append("ESXi Host IP")
            flag = True
        if not re.search(regex, row[5]):
            error.append("Invalid/blank IP")
            flag = True
        if not re.search(regex, row[6]):
            error.append("Netmask")
            flag = True
        if not re.search(regex, row[7]):
            error.append("Gateway")
            flag = True
        if not re.search(regex, row[8]):
            error.append("DNS")
            flag = True
        if not row[9]:
            error.append("Blank NTP")
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

        if flag:
            not_deployed[i + 1] = error

    csv_file.close()
    if flag:
        print("\n\nRow number(s) with incorrect/invalid input format: ")
        print(json.dumps(not_deployed, indent=6))
        print("\n\nPlease validate and re-run the script by correcting it/them.")
        print("Exiting...\n\n")
        exit()


if __name__ == "__main__":
    start_time = time.time()
    validation_check()  # Performing input validation checks

    csv_file = open("input_data.csv")
    csv_reader = csv.reader(csv_file)
    cols = next(csv_reader)
    results = {}

    pool = mp.Pool(processes=(mp.cpu_count() - 1))
    results = {row[5]: pool.apply_async(worker, row) for row in csv_reader}
    print(results)
    progress(results)

    # for i in results:
    # print(i, results.get(i).get())

    csv_file.close()
    end_time = time.time()
    print("\n****** TIME TAKEN FOR DEPLOYING THE VMNs {:0.2f} MINUTES ******\n".format((end_time - start_time) / 60))

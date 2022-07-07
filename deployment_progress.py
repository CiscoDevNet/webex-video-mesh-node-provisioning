import re
from time import sleep
import json
import os


def progress(data):
    file_name = 'vmn_provisioning.log'
    fh = open(file_name, 'r')
    disk_flag = {}
    task_flag = {}
    disk_percent = {}
    task_percent = {}
    disk_start = 0
    task_start = 0
    for i in data:
        disk_flag[i] = False
        task_flag[i] = False
        disk_percent[i] = '0%'
        task_percent[i] = '0%'

    disk_count = 0
    task_count = 0
    time_taken_count = 0
    n = len(disk_percent)
    os.system('clear')
    print("Process starting .....")
    killed_pids = set()
    failed_ip = set()
    progress = []

    failed_ips = list()
    passed_ips = list()

    # regex_search = r"ipaddress=^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
    regex_search = r'ipaddress=[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}'
    ip = ''
    while True:
        if time_taken_count == n or (disk_count == n and task_count == n):
            break
        line = fh.readline()
        if line:
            if re.search(r"Invalid target datastor", line):
                try:
                    ip = re.search(regex_search, line).group().split('=')[-1]
                    if ip in disk_percent:
                        del disk_percent[ip]
                        del task_percent[ip]
                        del disk_flag[ip]
                        del task_flag[ip]
                        n -= 1
                        time_taken_count -= 1
                        progress.append(f"{ip} could not be deployed due to Wrong Datastore Name.")
                        failed_ips.append(ip)
                except AttributeError:
                    continue
                else:
                    failed_ip.add(ip)
            if re.search(r"TIME TAKEN", line):
                time_taken_count += 1
            if re.search(r"Error: Invalid target name", line):
                try:
                    ip = re.search(regex_search, line).group().split('=')[-1]
                    if ip in disk_percent:
                        del disk_percent[ip]
                        del task_percent[ip]
                        del disk_flag[ip]
                        del task_flag[ip]
                        n -= 1
                        time_taken_count -= 1
                        progress.append(f"{ip} could not be deployed due to Wrong Internal/External Network Name.")
                        failed_ips.append(ip)
                except AttributeError:
                    continue
                else:
                    failed_ip.add(ip)
            if re.search(r"Error: Target datastore", line):
                try:
                    ip = re.search(regex_search, line).group().split('=')[-1]
                    if ip in disk_percent:
                        del disk_percent[ip]
                        del task_percent[ip]
                        del disk_flag[ip]
                        del task_flag[ip]
                        n -= 1
                        time_taken_count -= 1
                        progress.append(
                            f"{ip} could not be deployed because datastore is not accessible or the ESXi is down")
                        failed_ips.append(ip)
                except AttributeError:
                    continue
                else:
                    failed_ip.add(ip)

            if re.search(r"Error: Task failed on server: An error occurred while communicating with the remote host",
                         line):
                try:
                    ip = re.search(regex_search, line).group().split('=')[-1]
                    if ip in disk_percent:
                        del disk_percent[ip]
                        del task_percent[ip]
                        del disk_flag[ip]
                        del task_flag[ip]
                        n -= 1
                        time_taken_count -= 1
                        progress.append(f"{ip} could not be deployed - unable to communicate to ESXi")
                        failed_ips.append(ip)
                except AttributeError:
                    continue
                else:
                    failed_ip.add(ip)

            # If the ESXi communication stops during VMN deployment
            if re.search(r"Error: Operation was canceled", line):
                try:
                    # ip = re.search(regex_search, line).group().split('=')[-1]
                    if ip in disk_percent:
                        del disk_percent[ip]
                        del task_percent[ip]
                        del disk_flag[ip]
                        del task_flag[ip]
                        n -= 1
                        time_taken_count -= 1
                        esxi = line.split('/')[-1]
                        progress.append(f"{ip} could not be deployed - unable to communicate to ESXi")
                        failed_ips.append(ip)
                except AttributeError:
                    continue
                else:
                    failed_ip.add(ip)
            error_mat = re.search(r"b'[*]{30}'", line)
            if error_mat:
                try:
                    ip = re.search(regex_search, line).group().split('=')[-1]
                    process_id = int(re.search(r'Process\s+\d+', line).group().split()[-1])
                    if process_id not in killed_pids and ip in disk_percent:
                        os.kill(process_id, 9)
                        del disk_percent[ip]
                        del task_percent[ip]
                        del disk_flag[ip]
                        del task_flag[ip]
                        n -= 1
                        progress.append(f"{ip} could not be deployed due to Wrong ESXi Credentials.")
                        failed_ips.append(ip)
                except AttributeError:
                    continue
                else:
                    killed_pids.add(process_id)
                    failed_ip.add(ip)
            mat1 = re.search(r'(rDisk progress:\s+[0-9]+%|rTransfer Completed)', line)
            mat2 = re.search(r'(rTask progress:\s+[0-9]+%|rTask Completed)', line)
            if mat1:
                try:
                    ip = \
                        re.search(regex_search, line).group().split('=')[-1]
                except AttributeError:
                    continue
                if mat1.group() == 'rTransfer Completed':
                    disk_flag[ip] = True
                    disk_percent[ip] = '100%'
                    disk_count += 1
                else:
                    disk_start = 1
                    if not disk_flag[ip]:
                        disk_percent[ip] = (re.search(r'[0-9]+', mat1.group()).group()) + '%'
            elif mat2:
                try:
                    ip = \
                        re.search(r'ipaddress[_]*[1]*=[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}',
                                  line).group().split('=')[
                            -1]
                except AttributeError:
                    continue
                if mat2.group() == 'rTask Completed':
                    task_flag[ip] = True
                    task_percent[ip] = '100%'
                    task_count += 1
                else:
                    task_start = 1
                    if not task_flag[ip]:
                        task_percent[ip] = (re.search(r'[0-9]+', mat2.group()).group()) + '%'

                sleep(3)

            if disk_start:
                os.system('clear')
                if failed_ip:
                    print(
                        "\n\nSome machines won't be deployed due to some errors, check the summary in the end for more details : \n")
                    for fail in failed_ip:
                        print(fail, "\n")
                print(f"Deploying {n} VMNs")
                print("\nInstallation progress : ")
                print(json.dumps(disk_percent, indent=6), end='\n')
            if task_start:
                print("\n\nConfiguration progress : ")
                print(json.dumps(task_percent, indent=6), end='\n')

    fh.close()
    print('\n\nFinishing up, hold on. This might just take a few minutes...\n\n')

    for i in task_percent:
        if task_percent[i] != "100%":
            progress.append(f"{i} could not be deployed due to lack of resources in the ESXi server.")
            failed_ips.append(i)
        else:
            progress.append(f"{i} was successfully deployed.")
            passed_ips.append(i)
    for i in progress:
        print(i, "\n")

    return passed_ips, failed_ips

import csv
from time import sleep
from pyVim.connect import SmartConnectNoSSL


def host_validation():
    # Check if host credentials are different for same user
    csv_file = open("input_data.csv")
    csv_reader = csv.reader(csv_file)
    cols = next(csv_reader)
    host_dict = {}

    for i, row in enumerate(csv_reader):
        if row[0] in host_dict:
            if row[1] in host_dict[row[0]]:
                host_dict[row[0]][row[1]].add(row[2])
            else:
                host_dict[row[0]].update({row[1]: {row[2]}})
        else:
            host_dict[row[0]] = {row[1]: {row[2]}}

    pass_flag = False
    for host in host_dict:
        for user in host_dict[host]:
            if len(host_dict[host][user]) != 1:
                pass_flag = True
                print(
                    f"\nCredentials for host '{host}' for the user '{user}' are different at different rows. "
                    f"Please verify them and re-run.")

    if pass_flag:
        print('\nExiting...\n\n')
        exit(1)

    csv_file.close()

    print("\nPerforming authentication on host credentials\n")
    wrong_cred = []
    wrong_cred_flag = False
    for host in host_dict:
        for user in host_dict[host]:
            passwd = next(iter(host_dict[host][user]))
            try:
                si = SmartConnectNoSSL(host=host, user=user, pwd=passwd)
                if si is None:
                    print('Here')
                    wrong_cred.append((host, user, passwd))
                    wrong_cred_flag = True
            except BaseException:
                wrong_cred.append((host, user, passwd))
                wrong_cred_flag = True

    if wrong_cred_flag:
        print('\nWrong credentials:')
        for cred in wrong_cred:
            print("\n", cred)
        print("\nEnter correct credentials for all hosts, and then re-run the script.")
        print('\nExiting..')
        exit(1)

    else:
        print("Password authentication successful\n\n")

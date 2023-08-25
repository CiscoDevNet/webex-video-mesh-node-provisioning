import csv
import signal
from contextlib import contextmanager
from pyVim import connect

TIMEOUT = 20
MESSAGE = f'Could not connect. Timed-out after {TIMEOUT} seconds'


class TimeOutException(Exception):
    pass


@contextmanager
def time_out(seconds):
    def signal_handler(signum, frame):
        raise TimeOutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


def host_validation(input_file):
    # Check if host credentials are different for same user
    csv_file = open(input_file)
    csv_reader = csv.reader(csv_file)
    cols = next(csv_reader)
    host_dict = {}

    for i, row in enumerate(csv_reader):
        if len(row) > 1:
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

    print("\nPerforming authentication on host credentials....\n")
    wrong_cred = []
    connection_issue = []
    success = []
    exit_flag = False
    for host in host_dict:
        for user in host_dict[host]:
            passwd = next(iter(host_dict[host][user]))
            try:
                with time_out(TIMEOUT):
                    si = connect.SmartConnect(host=host, user=user, pwd=passwd, disableSslCertValidation=True)
                if si is None:
                    connection_issue.append(host)
                    exit_flag = True
            except TimeOutException:
                connection_issue.append(host)
                exit_flag = True
            except BaseException:
                wrong_cred.append((host, user, passwd))
                exit_flag = True
            else:
                success.append(host)

    if success:
        print('\nSuccessful:')
        for s in success:
            print(s)

    if exit_flag:
        print('\n** One or more validation failed. Re-run the script for failed IPs after fixing the issue.')
        print('** Below are the details.')
        if wrong_cred:
            print('\nWrong credentials:')
            for cred in wrong_cred:
                print(cred)
        if connection_issue:
            print('\nConnection issue:')
            for conn in connection_issue:
                print(f'{conn}:: {MESSAGE}')
        print('\nExiting..\n')
        exit(1)

import csv
import time
import argparse
import multiprocessing as mp
from time import sleep
from driver_guest_info import worker
from deployment_progress import progress
from utils import get_rows
from utils import mask_passwords
from validations.host_validation import host_validation
from validations.input_validation import validation_check
from validations.vcenter_validations import vcenter_check


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VMN Bulk provisioning")
    parser.add_argument('-m', action='store', dest='method', required=True, choices=['standalone', 'vcenter'], help='Method')
    args = parser.parse_args()
    method = args.method
    if method == 'standalone':
        file_name = "input_data.csv"
        print(f'\nChosen method is {method}. Deploying directly on ESXi\n')
    else:
        file_name = "input_data_vcenter.csv"
        print(f'\nChosen method is {method}. Deploying via Vcenter\n')

    print(f"Using file '{file_name}' as input")

    sleep(1)

    start_time = time.time()
    validation_check(file_name, method)  # Performing input validation checks
    host_validation(file_name)

    if method == 'vcenter':
        vcenter_check(file_name)

    csv_file = open(file_name)
    csv_reader = csv.reader(csv_file)
    cols = next(csv_reader)
    results = {}

    pool = mp.Pool(processes=(mp.cpu_count() - 1))
    results = {row[5]: pool.apply_async(worker, args=row, kwds={'method': method}) for row in csv_reader if len(row) > 1}
    passed, failed = progress(results, method)

    csv_file.close()
    end_time = time.time()
    out_time = end_time - start_time
    out_time = time.strftime('%H:%M:%S', time.gmtime(out_time))
    print("\n****** TIME TAKEN FOR DEPLOYING THE VMNs {} HOURS ******\n".format(out_time))

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

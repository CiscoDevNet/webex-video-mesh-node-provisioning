import csv
from validations.check_esxi import check_esxi_name


def vcenter_check(input_file):
    print("\nPerforming vCenter specific validations..")
    csv_file = open(input_file)
    csv_reader = csv.reader(csv_file)
    cols = next(csv_reader)
    not_deployed = {}
    flag = False

    for i, row in enumerate(csv_reader):
        error = []

        # ESXi validation
        if not row[14]:
            error.append("ESXi host not provided")
            flag = True
        else:
            if not check_esxi_name(row[0], row[1], row[2], row[14]):
                error.append("Invalid/wrong ESXi name")
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

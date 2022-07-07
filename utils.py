import csv


def mask_passwords(file_name, passed_rows, failed_rows, col_num=None, passed_masking_char='*', failed_masking_char='#'):
    if not col_num:
        return False

    try:
        csv_file = open(file_name)
        csv_reader = csv.reader(csv_file)
        cols = next(csv_reader)
        data = list(csv_reader)
        csv_file.close()

        for num, row in enumerate(data):
            if isinstance(col_num, int):
                if num in passed_rows and row[col_num]:
                    row[col_num] = passed_masking_char * 6
                elif num in failed_rows and row[col_num]:
                    row[col_num] = failed_masking_char * 6
            elif isinstance(col_num, list):
                for col in col_num:
                    if num in passed_rows and row[col]:
                        row[col] = passed_masking_char * 6
                    elif num in failed_rows and row[col]:
                        row[col] = failed_masking_char * 6

        csv_file = open(file_name, 'w')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(cols)
        csv_writer.writerows(data)
        csv_file.close()
        return True
    except Exception as err:
        return False


def get_rows(file_name, passed_ips, failed_ips, ip_col):
    passed_rows = list()
    failed_rows = list()
    try:
        csv_file = open(file_name)
        csv_reader = csv.reader(csv_file)
        cols = next(csv_reader)
        data = list(csv_reader)
        csv_file.close()

        for num, row in enumerate(data):
            if row[ip_col] in passed_ips:
                passed_rows.append(num)
            elif row[ip_col] in failed_ips:
                failed_rows.append(num)

        return passed_rows, failed_rows
    except Exception as err:
        return False

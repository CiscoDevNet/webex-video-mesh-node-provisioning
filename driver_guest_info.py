import json
import provision_vm_using_guest_info


def worker(*data):
    esxi_host = data[0]
    username = data[1]
    password = data[2]
    datastore_name = data[3]
    name = data[4]
    ip = data[5]
    mask = data[6]
    gateway = data[7]
    dns = data[8].replace('|', ',')
    ntp = data[9].replace('|', ',')
    hostname = data[10]
    esxi_internal_nw = data[11]
    esxi_external_nw = data[12]
    deployment_option = data[13]  # 'VMNLite' or 'CMS1000'

    with open('config.json', 'r') as fh:
        config_details = json.load(fh)

    ovf_filename = config_details['ovf_filename']
    vm_internal_nw = config_details['vm_internal_nw']
    vm_external_nw = config_details['vm_external_nw']
    dual_deployment = config_details['dual_ip_deployment']
    log_file = f"ovf_{ip}.log"

    if dual_deployment == "false":
        dual_ip_deployment = False
    else:
        dual_ip_deployment = True

    try:
        res = provision_vm_using_guest_info.deploy_ovf_with_guestinfo(esxi_host, username, password, ovf_filename, name,
                                                                      datastore_name, ip, mask, gateway, dns, ntp,
                                                                      hostname, deployment_option, vm_internal_nw,
                                                                      esxi_internal_nw, vm_external_nw,
                                                                      esxi_external_nw, dual_ip_deployment, log_file,
                                                                      'true')
    except Exception as err:
        return f"Some error occurred: {err}", f"Check {log_file} for more details"
    else:
        if res:
            return "Deployment was successful!"
        else:
            return "Deployment was NOT successful!"

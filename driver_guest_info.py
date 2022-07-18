import json
import provision_vm_using_guest_info
import provision_vm_vcenter
from get_esxi_path_on_vcenter import get_esxi_path


def worker(*data, method='standalone'):
    host = data[0]
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
        if method == 'vcenter':
            esxi_host = data[14]
            esxi_path = get_esxi_path(host, username, password, esxi_host)
            if esxi_path:
                res = provision_vm_vcenter.deploy_ovf_via_vcenter(host, username, password, esxi_host, esxi_path,
                                                                  ovf_filename, name, datastore_name, ip, mask, gateway,
                                                                  dns, ntp, hostname, deployment_option, vm_internal_nw,
                                                                  esxi_internal_nw, vm_external_nw, esxi_external_nw,
                                                                  dual_ip_deployment, log_file, 'true')
            else:
                print(f'{ip} could not be deployed - could not find ESXi {esxi_host} on vCenter {host}')
                return False
        else:
            res = provision_vm_using_guest_info.deploy_ovf_with_guestinfo(host, username, password, ovf_filename, name,
                                                                          datastore_name, ip, mask, gateway, dns, ntp,
                                                                          hostname, deployment_option, vm_internal_nw,
                                                                          esxi_internal_nw, vm_external_nw,
                                                                          esxi_external_nw, dual_ip_deployment,
                                                                          log_file,
                                                                          'true')
    except Exception as err:
        return f"Some error occurred: {err}", f"Check {log_file} for more details"
    else:
        if res:
            return "Deployment was successful!"
        else:
            return "Deployment was NOT successful!"

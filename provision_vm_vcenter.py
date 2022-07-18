import logging
import time
from log_format import LoggingFormatter

logging.basicConfig(filename='vmn_provisioning.log',
                    filemode='w',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

logging.info("Running VM Provisioning task")

logger = logging.getLogger('VM Provisioning')

try:
    from sh import ovftool
    from sh import base64
except ImportError:
    print()
    print("Please make sure python-sh module is installed")
    print("and ovftool is in the PATH")
    print()
    raise


def deploy_ovf_via_vcenter(vcenter_server, vcenter_user, vcenter_pass, esxi_host, esxi_path, ovf_filename, name,
                           datastore_name, ip, mask, gateway, dns, ntp, hostname, deployment_option, vm_internal_nw,
                           esxi_internal_nw, vm_external_nw, esxi_external_nw, dual_ip_deployment, log_file,
                           skip_manifest_check='false'):
    for h in logging.root.handlers:
        h.setFormatter(LoggingFormatter(h.formatter, patterns=[vcenter_pass]))
    try:
        logging.info(f"Creating VM on ESXi host {esxi_host} from ova file {ovf_filename} on vCenter {vcenter_server}")
        s = time.time()
        logging.info(f"ESXi host {esxi_host} local ova file {ovf_filename}: ")
        vm_name = f"--name={name}"
        mf_check = f"--skipManifestCheck={skip_manifest_check}"
        no_verify = f"--noSSLVerify"
        datastore = f"--datastore={datastore_name}"
        power_on = f"--powerOn=True"
        vm_net1 = f"--net:{vm_internal_nw}={esxi_internal_nw}"
        vm_net2 = f"--net:{vm_external_nw}={esxi_external_nw}"
        wait_ip = f"--X:waitForIp"
        overwrite = f"--overwrite"
        poweroff = f"--powerOffTarget"
        guest_opt1 = f"--prop:guestinfo.ciscoecp.nw.ipaddress={ip}"
        guest_opt2 = f"--prop:guestinfo.ciscoecp.nw.mask={mask}"
        guest_opt3 = f"--prop:guestinfo.ciscoecp.nw.gateway={gateway}"
        guest_opt4 = f"--prop:guestinfo.ciscoecp.nw.hostname={hostname}"
        guest_opt5 = f"--prop:guestinfo.ciscoecp.nw.dns={dns}"
        guest_opt6 = f"--prop:guestinfo.ciscoecp.nw.ntp={ntp}"
        inject_ovfenv_opt = f"--X:injectOvfEnv"
        logfile_opt = f"--X:logFile={log_file}"
        loglevel_opt = f"--X:logLevel=verbose"
        deployment_opt = f"--deploymentOption={deployment_option}"
        source = ovf_filename
        dest = f"vi://{vcenter_user}:{vcenter_pass}@{vcenter_server}/{esxi_path}"

        # we have to set power_on=True when using ovftool launch ova with ignite config,
        # so that config parameters can be saved into vm instance. We can not set power_on=False
        # because EXSi has no database to sore ingite config parameters.

        # Only if external network mapping is provided (for dual IP OVAs)
        # This option may not required for the HDS or old HMS OVA deployments
        if dual_ip_deployment:
            logging.info("Executing ovftool  {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {}".format( \
                vm_name, mf_check, no_verify, datastore, power_on, vm_net1, vm_net2, wait_ip, \
                overwrite, poweroff, inject_ovfenv_opt, logfile_opt, loglevel_opt, guest_opt1, guest_opt2, guest_opt3,
                guest_opt4, guest_opt5, guest_opt6, deployment_opt, source, dest))
            output = ovftool(vm_name, mf_check, no_verify, datastore, power_on, vm_net1, vm_net2, wait_ip, \
                             overwrite, poweroff, inject_ovfenv_opt, logfile_opt, loglevel_opt, guest_opt1, guest_opt2,
                             guest_opt3, guest_opt4, guest_opt5, guest_opt6, deployment_opt, source, dest)
        else:
            logging.info("Executing ovftool  {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {}".format( \
                vm_name, mf_check, no_verify, datastore, power_on, vm_net1, wait_ip, \
                overwrite, poweroff, inject_ovfenv_opt, logfile_opt, loglevel_opt, guest_opt1, guest_opt2, guest_opt3,
                guest_opt4, guest_opt5, guest_opt6, deployment_opt, source, dest))
            output = ovftool(vm_name, mf_check, no_verify, datastore, power_on, vm_net1, wait_ip, \
                             overwrite, poweroff, inject_ovfenv_opt, logfile_opt, loglevel_opt, guest_opt1, guest_opt2,
                             guest_opt3, guest_opt4, guest_opt5, guest_opt6, deployment_opt, source, dest)

        logging.info("output: {}".format(output))

        logging.debug("Test VM is created")
        time.sleep(60)
        return True
    except BaseException:
        logging.exception("exception in deploy_ovf_via_vcenter")
        return False
    finally:
        e = time.time()
        out_time = e - s
        out_time = time.strftime('%H:%M:%S', time.gmtime(out_time))
        print("\n****** TIME TAKEN FOR DEPLOYING THE VMNs {} HOURS ******\n".format(out_time))

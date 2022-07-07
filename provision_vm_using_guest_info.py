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


def deploy_ovf_with_guestinfo(esxi_host, username, password, ovf_filename, name, datastore_name, ip, mask, gateway, dns,
                              ntp, hostname, deployment_option, vm_internal_nw, esxi_internal_nw, vm_external_nw,
                              esxi_external_nw, dual_ip_deployment, log_file, skip_manifest_check='false'):
    for h in logging.root.handlers:
        h.setFormatter(LoggingFormatter(h.formatter, patterns=[password]))
    try:
        logging.info("Creating VM on ESXi host {} from ova file {}".format(esxi_host, ovf_filename))
        s = time.time()
        logging.info("ESXi host {} local ova file {}: ".format(esxi_host, ovf_filename))
        vm_name = "--name={}".format(name)
        mf_check = "--skipManifestCheck=" + skip_manifest_check
        no_verify = "--noSSLVerify"
        datastore = "--datastore={}".format(datastore_name)
        power_on = "--powerOn=True"
        vm_net1 = "--net:{}={}".format(vm_internal_nw, esxi_internal_nw)
        vm_net2 = "--net:{}={}".format(vm_external_nw, esxi_external_nw)
        wait_ip = "--X:waitForIp"
        overwrite = "--overwrite"
        poweroff = "--powerOffTarget"
        guest_opt1 = "--prop:guestinfo.ciscoecp.nw.ipaddress={}".format(ip)
        guest_opt2 = "--prop:guestinfo.ciscoecp.nw.mask={}".format(mask)
        guest_opt3 = "--prop:guestinfo.ciscoecp.nw.gateway={}".format(gateway)
        guest_opt4 = "--prop:guestinfo.ciscoecp.nw.hostname={}".format(hostname)
        guest_opt5 = "--prop:guestinfo.ciscoecp.nw.dns={}".format(dns)
        guest_opt6 = "--prop:guestinfo.ciscoecp.nw.ntp={}".format(ntp)
        inject_ovfenv_opt = "--X:injectOvfEnv"
        logfile_opt = "--X:logFile={}".format(log_file)
        loglevel_opt = "--X:logLevel=verbose"
        deployment_opt = "--deploymentOption={}".format(deployment_option)
        source = ovf_filename
        dest = "vi://{}:{}@{}".format(username, password, esxi_host)

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
        logging.exception("exception in deploy_ovf_with_guestinfo")
        return False
    finally:
        e = time.time()
        logging.debug("\n****** TIME TAKEN FOR DEPLOYING OVF {:0.2f} MINUTES ******\n".format((e - s) / 60))

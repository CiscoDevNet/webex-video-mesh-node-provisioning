from pyVim import connect


def check_esxi_name(vcenter, username, passwd, esxi_name):
    si = connect.SmartConnect(host=vcenter, user=username, pwd=passwd, disableSslCertValidation=True)
    content = si.RetrieveContent()

    host_list = []
    stack = [content.rootFolder]
    while stack:
        entity = stack.pop()
        if entity.__class__.__name__ == 'vim.HostSystem':
            host_list.append(entity)
        if hasattr(entity, 'host'):
            if isinstance(entity.host, list):
                for host in entity.host:
                    host_list.append(host)
            else:
                host_list.append(entity.host)
        if hasattr(entity, 'hostFolder'):
            stack.append(entity.hostFolder)
        if hasattr(entity, 'childEntity'):
            for child in entity.childEntity:
                stack.append(child)

    hosts = []
    for host in host_list:
        hosts.append(host.name)

    if esxi_name in hosts:
        return True
    return False

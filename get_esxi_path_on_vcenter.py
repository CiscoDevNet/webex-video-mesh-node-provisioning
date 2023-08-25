from pyVim import connect


def get_esxi_entity(vcenter, username, passwd, esxi_name):
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
                    if host.name == esxi_name:
                        return host
            else:
                return entity.host
        if hasattr(entity, 'hostFolder'):
            stack.append(entity.hostFolder)
        if hasattr(entity, 'childEntity'):
            for child in entity.childEntity:
                stack.append(child)
                if child.name == esxi_name:
                    return child


def get_parent(child_obj):
    entity = child_obj
    path = []
    while True:
        if entity.name == 'Datacenters':
            break
        parent_dir = entity.parent
        path.append(parent_dir.name)
        entity = parent_dir

    path = path[:-1]
    path.reverse()
    esxi_path = '/'.join(path)
    return esxi_path


def get_esxi_path(vcenter, user, password, esxi):
    esxi_entity = get_esxi_entity(vcenter, user, password, esxi)
    if esxi_entity:
        result = get_parent(esxi_entity)
        if result:
            result += '/' + esxi
            return result
        else:
            return False
    else:
        return False

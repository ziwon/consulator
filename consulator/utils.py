import netifaces

def get_host_ip(interface_name):
    addrs = netifaces.ifaddresses(interface_name)
    ips = [x['addr'] for x in addrs[netifaces.AF_INET]]
    return ips[0]
import netifaces


def get_host_ip(interface_name):
    return netifaces.ifaddresses(interface_name)[netifaces.AF_INET][0]["addr"]
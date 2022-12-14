import socket
import sys

import nmap
from ovos_plugin_manager.templates.iot import IOTDevicePlugin, IOTScannerPlugin


# Get your local network IP address. e.g. 192.168.178.X
def get_lan_ip():
    try:
        return ([(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in
                 [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1])
    except socket.error as e:
        sys.stderr.write(str(e) + "\n")  # probably offline / no internet connection
        sys.exit(e.errno)


class LanDevice(IOTDevicePlugin):
    def __init__(self, device_id, host, name="generic lan device", raw_data=None):
        device_id = device_id or f"lan:{host}"
        raw_data = raw_data or {"name": name, "description": "local network device"}
        super().__init__(device_id, host, name, raw_data)

    @property
    def as_dict(self):
        return {
            "host": self.host,
            "name": self.name,
            "model": self.product_model,
            "device_type": "local network device",
            "device_id": self.device_id,
            "state": self.is_on,
            "raw": self.raw_data
        }

    @property
    def product_model(self):
        return self.raw_data.get("model", "LAN device")


class LanPlugin(IOTScannerPlugin):
    def scan(self):
        hosts = str(".".join(get_lan_ip().split(".")[:-1])) + ".0/24"
        scanner = nmap.PortScanner()
        scanner.scan(hosts=hosts, arguments="-sn")

        for ip in scanner.all_hosts():
            name = scanner[ip].hostname()
            device_id = f"{ip}:{name}"
            yield LanDevice(device_id, ip, name, scanner[ip])

    def get_device(self, ip):
        for device in self.scan():
            if device.host == ip:
                return device
        return None


if __name__ == "__main__":
    from pprint import pprint

    for host in LanPlugin().scan():
        pprint(host.as_dict)

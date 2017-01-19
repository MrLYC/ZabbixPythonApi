# encoding: utf-8
import subprocess
import tempfile


class ZabbixSender(object):
    def __init__(self, server):
        self.server = server
        self.collected_file = tempfile.NamedTemporaryFile("w+b")
        self.status = None

    def collect(self, host, key, val):
        self.collected_file.write('"%s" "%s" "%s"\n' % (host, key, val))

    def send(self):
        self.collected_file.flush()
        self.status = subprocess.check_call([
            "zabbix_sender", "-z", self.server,
            "-i", self.collected_file.name,
        ])
        return self.status

    def __enter__(self):
        return self.collect

    def __exit__(self, typ, val, trbk):
        self.send()

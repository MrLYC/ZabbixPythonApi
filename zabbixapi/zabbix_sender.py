# encoding: utf-8

from collections import namedtuple, deque
import struct
import socket
import time

try:
    import simplejson as json
except ImportError:
    import json

ZabbixSessionHeader = namedtuple("ZabbixSessionHeader", [
    "header", "version", "length",
])
ZabbixSessionResponse = namedtuple("ZabbixSessionResponse", [
    "header", "data",
])


class RequestError(Exception):
    pass


def get_time(ts=None):
    ts = ts or time.time()
    clock = int(ts)
    ns = (ts - clock) * 1000000000
    return clock, ns


class ZabbixSession(object):
    HEADER = "ZBXD"
    VERSION = 1
    PORT = 10050
    HEADER_FMT = "<4sBq"
    MAX_READ_SIZE = 65535

    @classmethod
    def pack_header(cls, header):
        return struct.pack(
            cls.HEADER_FMT, header.header,
            header.version, header.length,
        )

    @classmethod
    def pack_json(cls, data):
        data = json.dumps(data, ensure_ascii=False)
        data = data.encode("utf-8")
        header = ZabbixSessionHeader(
            header=cls.HEADER, version=cls.VERSION, length=len(data),
        )
        return cls.pack_header(header) + data

    def __init__(self, server, port=None):
        self.server = server
        self.port = port or self.PORT
        self.header_offset = struct.calcsize(self.HEADER_FMT)
        self.socket = socket.socket()
        self._connected = None

    def __enter__(self):
        if not self._connected:
            self.connect()
        return self

    def __exit__(self, typ, val, trbk):
        self.close()

    def connect(self):
        self.socket.connect((self.server, self.port))
        self._connected = True

    def close(self):
        self.socket.close()
        self._connected = False

    def request(self, data):
        self.socket.write(self.pack_json(data))
        response = self.socket.read(self.MAX_READ_SIZE)
        if not response:
            raise RequestError()
        header_part = response[:self.header_offset]
        header = ZabbixSessionHeader(*struct.unpack(
            self.HEADER_FMT, header_part,
        ))
        return ZabbixSessionResponse(header, json.loads(
            response[self.header_offset: self.header_offset + header.length],
        ))

    def get_active_checks(self, host):
        return self.request({
            "request": "active checks",
            "host": host,
        })

    def send_agent_data(self, data):
        clock, ns = get_time(ts)
        return self.request({
            "request": "agent data",
            "data": data,
            "clock": clock,
            "ns": ns,
        })


class ZabbixSender(object):

    def __init__(self, server, port=10050):
        self.server = server
        self.port = port
        self.data = []

    def collect(self, host, key, value, ts=None):
        clock, ns = get_time(ts)
        self.data.append({
            "host": host,
            "key": key,
            "value": value,
            "clock": clock,
            "ns": ns,
        })

    def send(self):
        with ZabbixSession(self.server, self.port) as session:
            return session.send_agent_data(self.data)

    def __enter__(self):
        return self.collect

    def __exit__(self, typ, val, trbk):
        self.send()

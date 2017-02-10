# encoding: utf-8

from collections import namedtuple
import struct
import socket
import time
import re

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
ZabbixSenderResponse = namedtuple("ZabbixSenderResponse", [
    "header", "response", "data", "processed", "failed", "total", "seconds_spent",
])
ZabbixCheckResponse = namedtuple("ZabbixCheckResponse", [
    "header", "response", "data", "items",
])
ZabbixCheckItem = namedtuple("ZabbixCheckItem", [
    "key", "delay", "lastlogsize", "mtime",
])


class RequestError(Exception):
    pass


def get_time(ts=None):
    ts = ts or time.time()
    clock = int(ts)
    return clock


class ZabbixSession(object):
    HEADER = b"ZBXD"
    VERSION = 1
    PORT = 10051
    HEADER_FMT = "<4sBQ"
    MAX_READ_SIZE = 65535
    RESPONSE_PATTERN = re.compile((
        r"processed:\s*(?P<processed>\d+)\s*;\s*"
        r"failed:\s*(?P<failed>\d+)\s*;\s*"
        r"total:\s*(?P<total>\d+)\s*;\s*"
        r"seconds spent:\s*(?P<seconds_spent>[\d\.]+)\s*"
    ))

    @classmethod
    def pack_header(cls, header):
        return struct.pack(
            cls.HEADER_FMT, header.header,
            header.version, header.length,
        )

    @classmethod
    def pack_json(cls, data):
        data = json.dumps(data, ensure_ascii=True)
        header = ZabbixSessionHeader(
            header=cls.HEADER, version=cls.VERSION, length=len(data),
        )
        return cls.pack_header(header) + data.encode("ascii")

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
        self.socket.send(self.pack_json(data))
        response = self.socket.recv(self.MAX_READ_SIZE)
        if not response:
            raise RequestError()
        header_part = response[:self.header_offset]
        header = ZabbixSessionHeader(*struct.unpack(
            self.HEADER_FMT, header_part.encode("ascii"),
        ))
        return ZabbixSessionResponse(header, json.loads(
            response[self.header_offset: self.header_offset + header.length],
        ))

    def get_active_checks(self, host):
        result = self.request({
            "request": "active checks",
            "host": host,
        })
        data = result.data
        return ZabbixCheckResponse(
            header=result.header, data=data,
            response=data.get("response"),
            items=[
                ZabbixCheckItem(
                    key=i.get("key"),
                    delay=i.get("delay"),
                    lastlogsize=i.get("lastlogsize"),
                    mtime=i.get("mtime"),
                )
                for i in data["data"]
            ]
        )

    def send_data(self, data, ts=None):
        clock = get_time(ts)
        result = self.request({
            "request": "sender data",
            "data": data,
            "clock": clock,
        })
        data = result.data
        info_m = self.RESPONSE_PATTERN.search(data.get("info", ""))
        info = info_m.groupdict() if info_m else {}
        return ZabbixSenderResponse(
            header=result.header, data=data,
            response=data.get("response"),
            processed=info.get("processed"),
            failed=info.get("failed"),
            total=info.get("total"),
            seconds_spent=info.get("seconds_spent"),
        )


class ZabbixSender(object):

    def __init__(self, server, port=None):
        self.server = server
        self.port = port
        self.data = []
        self.result = None

    def collect(self, host, key, value, ts=None):
        clock = get_time(ts)
        self.data.append({
            "host": host,
            "key": key,
            "value": value,
            "clock": clock,
        })

    def send(self):
        with ZabbixSession(self.server, self.port) as session:
            return session.send_data(self.data)

    def __enter__(self):
        return self.collect

    def __exit__(self, typ, val, trbk):
        self.result = self.send()

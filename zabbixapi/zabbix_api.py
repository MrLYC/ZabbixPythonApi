#!/usr/bin/env python
# encoding: utf-8

"""Python zabbix api for 2.x

Author: Liu Yicong @YYgame, Zhuhai, China
Email: saber000@vip.qq.com
Date: 17, NOV, 2014
"""

import json
import random
try:
    from urllib2 import Request, urlopen, URLError
except ImportError:
    from urllib.request import Request, urlopen, URLError


class ZabbixAPIException(Exception):
    pass


class APIItem(object):
    def __init__(self, zapi, name):
        self.__zapi = zapi
        self.__name = name.lower()

    def __call__(self, args=(), **params):
        if not self.__name:
            raise ZabbixAPIException("required method is empty")

        params.update(args)
        try:
            _id, data = self.__zapi.pack_params(self.__name, params)
            json_data = self.__zapi.post(data)
        except URLError as err:
            raise ZabbixAPIException(err.reason)

        try:
            content = json.loads(json_data)
        except ValueError as err:
            raise ZabbixAPIException(*err.args)

        result = content.get("result")
        if result is None:
            try:
                err = content["error"]["data"]
                raise ZabbixAPIException(err)
            except KeyError as err:
                raise ZabbixAPIException(err)
        return result

    def __getattr__(self, name):
        item = APIItem(self.__zapi, "%s.%s" % (self.__name, name))
        setattr(self, name, item)
        return item


class ZabbixAPI(object):
    POST_HEADERS = {
        "Content-Type": "application/json-rpc",
        "User-Agent": "python/zabbix_api",
    }

    def __init__(self, url):
        self.url = url
        self.auth = ""

    def __getattr__(self, name):
        item = APIItem(self, name)
        setattr(self, name, item)
        return item

    def pack_params(self, name, params):
        """Parse params to zabbix params json.

        Args:
            params: params dict object to pack.

        Return:
            json string.
        """
        _id = random.randint(1, 65565)
        post_params = {
            "jsonrpc": "2.0",
            "method": name,
            "params": params,
            "id": _id,
            "auth": self.auth,
        }

        if not self.islogin():
            post_params.pop("auth")

        return _id, json.dumps(post_params)

    def post(self, data):
        """Post json to url and try to fetch result as json

        Args:
            params: data to post.

        Return:
            response data from server
        """
        request = Request(self.url, data, self.POST_HEADERS.copy())
        response = urlopen(request)
        recv_data = response.read()
        return recv_data

    def islogin(self):
        """Check if has been loged.
        """
        return self.auth != ""

    def login(self, user, passwd):
        """Login to zabbix.

        Args:
            user: user name.
            passwd: password.
        """
        if not self.islogin():
            self.auth = self.user.login({
                "user": user,
                "password": passwd,
            })

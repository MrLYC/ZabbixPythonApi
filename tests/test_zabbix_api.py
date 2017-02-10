# encoding: utf-8

import json
from unittest import TestCase

import mock

from zabbixapi import zabbix_api


class TestZabbixAPIBase(TestCase):
    def setUp(self):
        self.user = "admin"
        self.password = "password"
        self.url = "https://zabbix.example.com/api_jsonrpc.php"
        self.urlopen_patch = mock.patch("zabbixapi.zabbix_api.urlopen")
        self.urlopen_mock = self.urlopen_patch.start()
        self.api = zabbix_api.ZabbixAPI(self.url)
        self.api.user.login = mock.MagicMock(return_value=str(id(self)))

    def tearDown(self):
        self.urlopen_patch.stop()


class APIItem(TestCase):
    def test_call(self):
        api_mock = mock.MagicMock()
        api_mock.pack_params.return_value = (1, "")
        api_mock.post.return_value = '{"result": 1}'

        item = zabbix_api.APIItem(api_mock, "")
        with self.assertRaises(zabbix_api.ZabbixAPIException):
            item()
        api_mock.post.assert_not_called()
        item = zabbix_api.APIItem(api_mock, "test")
        item()
        api_mock.post.assert_called()


class TestZabbixAPI(TestZabbixAPIBase):
    def test_construction(self):
        self.assertFalse(self.api.islogin())
        self.api.login(self.user, self.password)
        self.assertTrue(self.api.islogin())

    def test_request(self):
        self.api.login(self.user, self.password)
        data = [
            {
                "hostid": "10085",
                "groups": [
                    {
                        "groupid": "2",
                        "name": "Linux servers",
                        "internal": "0",
                        "flags": "0"
                    },
                    {
                        "groupid": "4",
                        "name": "Zabbix servers",
                        "internal": "0",
                        "flags": "0"
                    },
                ],
            },
        ]
        self.urlopen_mock.return_value = mock.MagicMock(
            read=mock.MagicMock(return_value=json.dumps({
                "jsonrpc": "2.0",
                "result": data,
                "id": None,
            })),
        )
        result = self.api.host.get({
            "output": ["hostid"],
            "selectGroups": "extend",
            "filter": {
                "host": ["Zabbix server"],
            },
        })
        self.assertEqual(result, data)

    def test_request_error(self):
        reason = "test %s" % id(self)
        self.urlopen_mock.side_effect = zabbix_api.URLError(reason)
        with self.assertRaisesRegexp(zabbix_api.ZabbixAPIException, reason):
            self.api.host.get({})

    def test_result_error(self):
        self.urlopen_mock.return_value = mock.MagicMock(
            read=mock.MagicMock(return_value="odd json"),
        )
        with self.assertRaises(zabbix_api.ZabbixAPIException):
            self.api.host.get({})

    def test_error_result(self):
        errmsg = "No groups for host \"Linux server\"."
        self.urlopen_mock.return_value = mock.MagicMock(
            read=mock.MagicMock(return_value=json.dumps({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32602,
                    "message": "Invalid params.",
                    "data": errmsg,
                },
                "id": None,
            })),
        )
        with self.assertRaisesRegexp(zabbix_api.ZabbixAPIException, errmsg):
            self.api.host.create({})

    def test_odd_error_result(self):
        self.urlopen_mock.return_value = mock.MagicMock(
            read=mock.MagicMock(return_value=json.dumps({
                "jsonrpc": "2.0",
                "id": None,
            })),
        )
        with self.assertRaises(zabbix_api.ZabbixAPIException):
            self.api.host.create({})

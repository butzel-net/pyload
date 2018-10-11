# -*- coding: utf-8 -*-
# @author: mkaay, RaNaN

from builtins import _, object
from threading import Lock

from pyload.network.Browser import Browser
from pyload.network.Bucket import Bucket
from pyload.network.CookieJar import CookieJar
from pyload.network.HTTPRequest import HTTPRequest
from pyload.network.XDCCRequest import XDCCRequest


class RequestFactory(object):
    def __init__(self, core):
        self.lock = Lock()
        self.core = core
        self.bucket = Bucket()
        self.updateBucket()
        self.cookiejars = {}

    def iface(self):
        return self.core.config["download"]["interface"]

    def getRequest(self, pluginName, account=None, type="HTTP", **kwargs):
        self.lock.acquire()

        options = self.getOptions()
        options.update(kwargs)  # submit kwargs as additional options

        if type == "XDCC":
            req = XDCCRequest(self.bucket, options)

        else:
            req = Browser(self.bucket, options)

            if account:
                cj = self.getCookieJar(pluginName, account)
                req.setCookieJar(cj)
            else:
                req.setCookieJar(CookieJar(pluginName))

        self.lock.release()
        return req

    def getHTTPRequest(self, **kwargs):
        """ returns a http request, dont forget to close it ! """
        options = self.getOptions()
        options.update(kwargs)  # submit kwargs as additional options
        return HTTPRequest(CookieJar(None), options)

    def getURL(self, *args, **kwargs):
        """ see HTTPRequest for argument list """
        h = HTTPRequest(None, self.getOptions())
        try:
            rep = h.load(*args, **kwargs)
        finally:
            h.close()

        return rep

    def getCookieJar(self, pluginName, account=None):
        if (pluginName, account) in self.cookiejars:
            return self.cookiejars[(pluginName, account)]

        cj = CookieJar(pluginName, account)
        self.cookiejars[(pluginName, account)] = cj
        return cj

    def getProxies(self):
        """ returns a proxy list for the request classes """
        if not self.core.config["proxy"]["proxy"]:
            return {}
        else:
            type = "http"
            setting = self.core.config["proxy"]["type"].lower()
            if setting == "socks4":
                type = "socks4"
            elif setting == "socks5":
                type = "socks5"

            username = None
            if self.core.config["proxy"]["username"] and self.core.config["proxy"]["username"].lower(
            ) != "none":
                username = self.core.config["proxy"]["username"]

            pw = None
            if self.core.config["proxy"]["password"] and self.core.config["proxy"]["password"].lower(
            ) != "none":
                pw = self.core.config["proxy"]["password"]

            return {
                "type": type,
                "address": self.core.config["proxy"]["address"],
                "port": self.core.config["proxy"]["port"],
                "username": username,
                "password": pw,
            }

    def getOptions(self):
        """returns options needed for pycurl"""
        return {"interface": self.iface(),
                "proxies": self.getProxies(),
                "ipv6": self.core.config["download"]["ipv6"]}

    def updateBucket(self):
        """ set values in the bucket according to settings"""
        if not self.core.config["download"]["limit_speed"]:
            self.bucket.setRate(-1)
        else:
            self.bucket.setRate(self.core.config["download"]["max_speed"] * 1024)


# needs pyreq in global namespace
def getURL(*args, **kwargs):
    return pyreq.getURL(*args, **kwargs)


def getRequest(*args, **kwargs):
    return pyreq.getHTTPRequest()
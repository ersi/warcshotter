#!/usr/bin/python

import warc
from urllib2 import HTTPHandler, build_opener
from httplib import HTTPConnection
from sys import argv
from datetime import datetime
from urlparse import urlparse
from socket import gethostbyname

REQUESTS = [] #FIXME: Don't rely on global list

# With help from http://stackoverflow.com/questions/603856/how-do-you-get-default-headers-in-a-urllib2-request
class MyHTTPConnection(HTTPConnection):
    def send(self, s):
        #FIXME: Don't rely on global list
        #FIXME: Add WARC-TARGET-URI to headers
        REQUESTS.append(warc.WARCRecord(payload=s,
                                        headers={"WARC-Type": "request"}))
        HTTPConnection.send(self, s)

class MyHTTPHandler(HTTPHandler):
    def http_open(self, req):
        return self.do_open(MyHTTPConnection, req)

def main():
    targeturl = argv[1]
    filename = "%s-%s.warc" % (urlparse(targeturl).netloc, 
                               datetime.utcnow().strftime("%Y%m%d-%H%M"))
    wf = warc.open(filename, "w")

    opener = build_opener(MyHTTPHandler)
    req = opener.open(targeturl)
    resp = req.read()

    if len(REQUESTS):
        wf.write_record(REQUESTS.pop(0))

    if req.getcode() == "200":
        resp_status = "HTTP/1.1 200 OK\r\n" #FIXME: How do we know it's http/1.1?
    else:
        resp_status = "HTTP/1.1 %s\r\n" % req.getcode() #FIXME:No desc after code
    payload = resp_status + str(req.info()) + '\r\n' + resp
    headers = {"WARC-Type": "response",
               "WARC-IP-Address": gethostbyname(urlparse(req.geturl()).netloc),
               "WARC-Target-URI": req.geturl()}
    record = warc.WARCRecord(payload=payload, headers=headers)
    wf.write_record(record)

    wf.close()

if __name__ == "__main__":
    main()

#!/usr/bin/python

import warc
from urllib2 import HTTPHandler, build_opener
from httplib import HTTPConnection
from sys import argv
from datetime import datetime
from urlparse import urlparse, urljoin
from socket import gethostbyname
from HTMLParser import HTMLParser 

REQUESTS = [] #FIXME: Don't rely on global list
TARGETS = []
DEBUG = True 
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

class MyHTMLParser(HTMLParser):
    def handle_starttag(self,tag, attrs):
        if tag == 'link':
            print "link ", attrs
            for attr in attrs:
                if "href" in attr[0]:
                    aurl = urlparse(attr[1])
                    purl = unicode(urljoin(argv[1], attr[1]))
                    TARGETS.append(purl)
                else:
                    pass
        elif tag == 'img':
            print "img ", attrs
            for attr in attrs:
                if "src" in attr[0]:
                    aurl = urlparse(attr[1])
                    purl = unicode(urljoin(argv[1], attr[1]))
                    TARGETS.append(purl)
                else:
                    pass
        elif tag == 'script':
            print "script ", attrs
            for attr in attrs:
                if "src" in attr[0]:
                    aurl = urlparse(attr[1])
                    purl = unicode(urljoin(argv[1], attr[1]))
                    TARGETS.append(purl)
                else:
                    pass

def download(url):
    if DEBUG:
        print "Trying to download %s..." % url
    opener = build_opener(MyHTTPHandler)
    request = opener.open(url)
    response = request.read()

    if request.getcode() == "200":
        resp_status = "HTTP/1.1 200 OK\r\n" #FIXME: How do we know it's http/1.1?
    else:
        resp_status = "HTTP/1.1 %s OK\r\n" % request.getcode()
    payload = resp_status + str(request.info()) + '\r\n' + response
    headers = {"WARC-Type": "response",
               "WARC-IP-Address": gethostbyname(urlparse(request.geturl()).netloc),
               "WARC-Target-URI": request.geturl()}
    record = warc.WARCRecord(payload=payload, headers=headers)

    if len(TARGETS) == 0:
        if DEBUG:
            print "TARGETS was empty.. so trying to parse..."
        parser = MyHTMLParser()
        parser.feed(response)
        if DEBUG:
            print "TARGETS: %r" % TARGETS

    return record

def main():
    if DEBUG:
        print "Starting..."
    targeturl = argv[1]
    filename = "%s-%s.warc" % (urlparse(targeturl).netloc, 
                               datetime.utcnow().strftime("%Y%m%d-%H%M"))
    wf = warc.open(filename, "w")

    if len(REQUESTS):
        wf.write_record(REQUESTS.pop(0))

    wf.write_record(download(targeturl))

    if DEBUG:
        print "Downloading linked content..."
    for target in TARGETS:
        if len(REQUESTS):
            wf.write_record(REQUESTS.pop(0))
        wf.write_record(download(target))
    if DEBUG:
        print "TARGETS ", TARGETS
    wf.close()

if __name__ == "__main__":
    main()

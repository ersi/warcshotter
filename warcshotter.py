#!/usr/bin/python

import warc
from urllib2 import HTTPHandler, build_opener
from httplib import HTTPConnection
from sys import argv
from datetime import datetime
from urlparse import urlparse, urljoin
from socket import gethostbyname
from HTMLParser import HTMLParser 

#FIXME: Don't rely on globals
REQUESTS = []
TARGETS = []
DEBUG = True

# With help from http://stackoverflow.com/questions/603856/how-do-you-get-default-headers-in-a-urllib2-request
class MyHTTPConnection(HTTPConnection):
    def send(self, s):
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

def create_warcinfo(filename):
    headers = {"WARC-Type": "warcinfo",
               "WARC-Filename": filename}
    payload = "software: Warcshotter\r\n
               format: WARC File Format 1.0\r\n
               conformsTo: http://bibnum.bnf.fr/WARC/WARC_ISO_28500_version1_latestdraft.pdf"
    record = warc.WARCRecord(payload=payload, headers=headers)
    return record

def main():
    if DEBUG:
        print "Starting..."
    targeturl = argv[1]
    filename = "%s-%s.warc" % (urlparse(targeturl).netloc, 
                               datetime.utcnow().strftime("%Y%m%d-%H%M"))
    wf = warc.open(filename, "w")

    warcinfo_record = create_warcinfo(filename)
    print "Writing warcinfo record"
    wf.write_record(warcinfo_record)

    record = download(targeturl)
    if len(REQUESTS):
        print "Writing request record."
        wf.write_record(REQUESTS.pop(0))
        print "Writing response record"
        wf.write_record(record)
    else:
        print "Writing response record"
        wf.write_record(record)
    if DEBUG:
        print "Downloading linked content..."
    for target in TARGETS:
        record = download(target)

        if len(REQUESTS):
            print "Writing request record"
            wf.write_record(REQUESTS.pop(0))
            print "Writing response record"
            wf.write_record(record)
        else:
            record = download(target)
            "Writing response record."
            wf.write_record(record)
    if DEBUG:
        print "TARGETS ", TARGETS
    wf.close()

if __name__ == "__main__":
    main()

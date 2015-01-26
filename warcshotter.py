#!/usr/bin/python

import warc
from urllib2 import HTTPHandler, HTTPSHandler, HTTPError, build_opener
from httplib import HTTPConnection, HTTPSConnection
from sys import argv
from datetime import datetime
from urlparse import urlparse, urljoin
from socket import gethostbyname
from HTMLParser import HTMLParser, HTMLParseError

REQUESTS = []
TARGETS = []
DEBUG = True


class MyHTTPConnection(HTTPConnection):
    def send(self, s):
        REQUESTS.append(warc.WARCRecord(payload=s,
                                        headers={"WARC-Type": "request"}))
        HTTPConnection.send(self, s)


class MyHTTPHandler(HTTPHandler):
    def http_open(self, req):
        return self.do_open(MyHTTPConnection, req)


class MyHTTPSConnection(HTTPSConnection):
    def send(self, s):
        REQUESTS.append(warc.WARCRecord(payload=s,
                                        headers={"WARC-Type": "request"}))
        HTTPSConnection.send(self, s)


class MyHTTPSHandler(HTTPSHandler):
    def https_open(self, req):
        return self.do_open(MyHTTPSConnection, req)


class MyHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if DEBUG:
            if tag in ["link", "img", "script", "iframe", "embed"]:
                print "%s - %r" % (tag, attrs)
        if tag == 'link':
            for attr in attrs:
                if "href" in attr[0]:
                    url = unicode(urljoin(argv[1], attr[1]))
                    if url not in TARGETS:
                        TARGETS.append(url)
                    else:
                        pass
                else:
                    pass
        elif tag in ["img", "script"]:
            for attr in attrs:
                if "src" in attr[0]:
                    url = unicode(urljoin(argv[1], attr[1]))
                    if url not in TARGETS:
                        TARGETS.append(url)
                    else:
                        pass
                else:
                    pass


def parsehtml(htmlresponse):
    htmlparser = MyHTMLParser()
    htmlparser.feed(htmlresponse)


def download(url):
    if DEBUG:
        print "Trying to download %s" % url
    if urlparse(url).scheme == "https":
        opener = build_opener(MyHTTPSHandler)
    else:
        opener = build_opener(MyHTTPHandler)
    try:
        request = opener.open(url)
        response = request.read()
    except HTTPError, error:
        request = error
        response = request.read()

    resp_status = "HTTP/1.1 %s %s\r\n" % (request.getcode(), request.msg)
    payload = resp_status + str(request.info()) + '\r\n' + response
    headers = {"WARC-Type": "response",
               "WARC-IP-Address": gethostbyname(urlparse(request.geturl()).netloc),
               "WARC-Target-URI": request.geturl()}
    record = warc.WARCRecord(payload=payload, headers=headers)

    if len(TARGETS) == 0:
        if DEBUG:
            print "TARGETS was empty.. so trying to parse"
        try:
            parsehtml(response)
        except HTMLParseError, e:
            pass
        if DEBUG:
            print "TARGETS: %r" % TARGETS

    return record


def mkwarcinfo(filename):
    headers = {"WARC-Type": "warcinfo",
               "WARC-Filename": filename}
    payload = ("software: Warcshotter\r\nformat: WARC File Format 1.0\r\n"
               "conformsTo: http://bibnum.bnf.fr/WARC/WARC_ISO_28500_version1_"
               "latestdraft.pdf")
    record = warc.WARCRecord(payload=payload, headers=headers)
    return record


def main():
    targeturl = argv[1]
    filename = "%s-%s.warc" % (urlparse(targeturl).netloc,
                               datetime.utcnow().strftime("%Y%m%d-%H%M"))
    print "Starting snapshot of %s, writing to %s" % (targeturl, filename)
    wf = warc.open(filename, "w")

    warcinfo_record = mkwarcinfo(filename)
    if DEBUG:
        print "Writing warcinfo record"
    wf.write_record(warcinfo_record)

    record = download(targeturl)
    if len(REQUESTS):
        request_record = REQUESTS.pop(0)
        if DEBUG:
            print "Writing request record %s" % request_record['WARC-Record-ID']
        wf.write_record(request_record)
        if DEBUG:
            print "Writing response record %s" % record['WARC-Record-ID']
        wf.write_record(record)
    else:
        if DEBUG:
            print "Writing response record"
        wf.write_record(record)

    # If the parser could parse the first resource, continue to download found
    # resources. Doesn't parse again, currently. Only grabbin images, css etc
    if DEBUG:
        print "Downloading linked content"
    for target in TARGETS:
        record = download(target)

        if len(REQUESTS):
            request_record = REQUESTS.pop(0)
            if DEBUG:
                print "Writing request record %s" % request_record['WARC-Record-ID']
            wf.write_record(request_record)
            if DEBUG:
                print "Writing response record %s" % record['WARC-Record-ID']
            wf.write_record(record)
        else:
            record = download(target)
            if DEBUG:
                "Writing response record."
            wf.write_record(record)
    if DEBUG:
        print "TARGETS ", TARGETS
    wf.close()
    print "Done."

if __name__ == "__main__":
    main()

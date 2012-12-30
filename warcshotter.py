#!/bin/python

# Open a new file  
# Write a warcinfo record
# Open a connection to target site / Fetch the original designated resource
# If the resource is HTML, parse the resource for further direct linked resources - like image srcs, script srcs, link/anchor hrefs,
#

import warc, urllib2
from urllib2 import urlopen
from sys import argv
from datetime import datetime
from urlparse import urlparse
from socket import gethostbyname

def main():
    targeturl = argv[1]
    filename = "%s-%s.warc" % (urlparse(targeturl).netloc, 
                               datetime.utcnow().strftime("%Y%m%d-%H%M"))
    f = warc.open(filename, "w")

    req = urlopen(targeturl)
    resp = req.read()

    payload = str(req.info()) + '\r\n' + resp
    headers = {"WARC-Type": "response",
               "WARC-IP-Address": gethostbyname(urlparse.(req.geturl()).netloc)}
    record = warc.WARCRecord(payload=payload, headers=headers)
    f.write_record(record)

    f.close()
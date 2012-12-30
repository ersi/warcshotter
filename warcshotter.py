#!/bin/python

# Open a new file  
# Write a warcinfo record
# Open a connection to target site / Fetch the original designated resource
# If the resource is HTML, parse the resource for further direct linked resources - like image srcs, script srcs, link/anchor hrefs,

import warc
from urllib2 import urlopen
from sys import argv
from datetime import datetime
from urlparse import urlparse
from socket import gethostbyname

def main():
    targeturl = argv[1]
    filename = "%s-%s.warc" % (urlparse(targeturl).netloc, 
                               datetime.utcnow().strftime("%Y%m%d-%H%M"))
    wf = warc.open(filename, "w")

    req = urlopen(targeturl)
    resp = req.read()

    payload = str(req.info()) + '\r\n' + resp
    headers = {"WARC-Type": "response",
               "WARC-IP-Address": gethostbyname(urlparse(req.geturl()).netloc)}
    record = warc.WARCRecord(payload=payload, headers=headers)
    wf.write_record(record)

    wf.close()

if __name__ == "__main__":
    main()

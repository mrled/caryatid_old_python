#!/usr/bin/env python3

# CARYATID:
# In architecture, an Atlas [https://atlas.hashicorp.com/] is a man taking the place of a column, and a Caryatid is a woman taking the place of a column

# - Receive one artifact as an argument
# - Hash it
# - Upload it to the web
# - Add it to catalog
# - Push catalog

import argparse
import datetime
import hashlib
import hmac
import json
import os
import requests
import subprocess
import sys
import time


scriptdir = os.path.dirname(os.path.realpath(__file__))
debug = False


def strace():
    import pdb
    pdb.set_trace()


def debugprint(message):
    global debug
    if debug:
        print(message)


def resolvepath(path):
    return os.path.realpath(os.path.normpath(os.path.expanduser(path)))


# Sample artifact catalog:
#
#
# {
#     "name": "devops",
#     "description": "This box contains Ubuntu 14.04.2 LTS 64-bit.",
#     "versions": [{
#         "version": "0.1.0",
#         "providers": [{
#                 "name": "virtualbox",
#                 "url": "file://~/VagrantBoxes/devops_0.1.0.box",
#                 "checksum_type": "sha1",
#                 "checksum": "d3597dccfdc6953d0a6eff4a9e1903f44f72ab94"
#         }]
#     }]
# }

def addbox2catalog(boxname, boxdescription, boxversion, boxurl, boxchecksumtype, boxchecksum, catalogpath, providername):
    catalogpath = resolvepath(catalogpath)

    # If the file doesn't exist, make it an empty json document
    if not (os.path.isdir(catalogpath)):
        with open(catalogpath, 'w') as c:
            c.write('{}')
        # raise Exception("No such catalog file '{}'".format(catalogpath))

    with open(catalogpath) as c:
        catalogdata = json.load(c)

    catalogdata['name'] = boxname
    catalogdata['description'] = boxdescription
    if 'versions' not in catalogdata.keys():
        catalogdata['versions'] = []

    for v in catalogdata.versions:
        if boxversion == v.version:
            versionmetadata = v
    else:
        versionmetadata = {'version': boxversion, 'providers': []}
        catalogdata.versions += [versionmetadata]

    # Remove any existing providers with the same name, and add a new one
    versionmetadata.providers[:] = [p for p in versionmetadata.providers if p['name'] != providername]
    versionmetadata.providers += [{'name': providername, 'url': boxurl, 'checksum_type': boxchecksumtype, 'checksum': boxchecksum}]


def rfc2822now():
    zone = time.altzone if time.localtime(time.time()).tm_isdst and time.daylight else time.timezone
    offsethours = int(abs(zone) / 60 / 60)
    offsetminutes = int(abs(zone) / 60 % 60)
    sign = '-' if zone == abs(zone) else '+'
    offset = "{}{:0<2}{:0<2}".format(sign, offsethours, offsetminutes)
    rfc2822 = datetime.datetime.strftime(datetime.datetime.now(), '%a, %d %b %Y %H:%M:%S {}'.format(offset))
    return rfc2822


def uploadbox2aws(localboxpath, s3filename, s3bucket, s3key):
    localboxpath = resolvepath(localboxpath)
    # e.g. Mon, 07 Nov 2016 19:32:05 +0000
    datestamp = rfc2822now()
    puturl = 'https://{}.s3.amazonaws.com/{}'.format(s3bucket, s3filename)
    contenttype = 'application/zip'
    resource = '/{}/{}'.format(s3bucket, s3filename)
    stringtosign = "PUT\n\n{}\n{}\n{}".format(contenttype, datestamp, resource)
    # untested. ugh. see here: http://www.jamesransom.net/uploading-a-file-using-curl-to-s3-aws/
    s3signature = hmac.new(s3key, msg=stringtosign, digestmode=hashlib.sha1)
    headers = {
        'Host': '{}.s3.amazonaws.com'.format(s3bucket),
        'Date': datestamp,
        'Content-Type': contenttype,
        'Authorization': 'AWS {}:{}'.format(s3key, s3signature)
    }
    with open(localboxpath, 'rb') as box:
        response = requests.put(puturl, data=box, headers=headers)
    if response.status_code != 200:
        raise Exception("Failed to upload to s3: status code '{}: {}'".format(response.status_code, response.reason))


def main(*args, **kwargs):
    parser = argparse.ArgumentParser(
        description="Add box built with packer to a vagrant catalog")

    parser.add_argument(
        "-d", action='store_true', dest='debug',
        help="Include debugging output")
    parser.add_argument(
        "artifact",
        help="The artifact we are being passed")

    parsed = parser.parse_args()
    if parsed.debug:
        global debug
        debug = True

    artifact = resolvepath(parsed.artifact)
    splart = os.path.basename(artifact).split(".")
    if splart[-1] == "box":
        boxtype = splart[-2]
        if boxtype == "virtualbox":
            pass
        else:
            raise Exception("Found a box of type '{}' but don't know how to process it".format(boxtype))
    else:
        debugprint("Passed an artifact named '{}'; nothing to do".format(artifact))

    raise Exception("Haven't yet gotten all the arguments we need, haven't yet called any of my functions for uploading or anything")


# if __name__ == '__main__':
#     sys.exit(main(*sys.argv))

addbox2catalog(boxname, boxdescription, boxversion, boxurl, boxchecksumtype, boxchecksum, catalogpath, providername)

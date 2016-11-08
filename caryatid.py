#!/usr/bin/env python3

# CARYATID:
# In architecture, an Atlas [https://atlas.hashicorp.com/] is a man taking the place of a column, and a Caryatid is a woman taking the place of a column

# - Receive one artifact as an argument
# - Hash it
# - Upload it to the web
# - Add it to catalog
# - Push catalog

import contextlib
import datetime
import hashlib
import hmac
import json
import os
import requests
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


@contextlib.contextmanager
def open2(pathorfile, mode):
    """Given either a (string) path or a file-like object, return a file-like object
    Intended for functions to use instead of builtin `open()` so that I can pass either
    """

    def suitablefile(pathorfile, mode):
        if 'r' in mode and not hasattr(pathorfile, 'read'):
            return False
        if 'w' in mode and not hasattr(pathorfile, 'write'):
            return False
        return True

    if suitablefile(pathorfile, mode):
        f = pathorfile
        toclose = None
    else:
        f = toclose = open(resolvepath(pathorfile), mode)

    try:
        yield f
    finally:
        if toclose:
            toclose.close()
        else:
            f.flush()


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

def addbox2catalog(boxname, boxdescription, boxversion, boxurl, boxchecksumtype, boxchecksum, catalogtext, providername):
    """Add a new Vagrant box to a catalog file

    Catalog files are one per box, with multiple versions. So there may be a catalog file for a box named "webserver", with versions 0.0.1, 0.0.2, etc.

    Arguments:
    boxname -- The name of the box
    boxdescription -- A description of the box
    boxurl -- The URL that vagrant will fetch the box from
    boxchecksumtype -- The type of checksum, such as 'sha1'
    boxchecksum -- The checksum itself
    catalogfile -- Either a path to, or a file-like object representing, the Vagrant catalog file
    providername -- The provider name, such as 'virtualbox'
    """

    if len(catalogtext) == 0:
        catalogdata = json.loads('{}')
    else:
        try:
            catalogdata = json.loads(catalogtext)
        except Exception as e:
            raise Exception("Could not decode catalog text:\r\n{}\r\nbecause of error '{}'".format(catalogtext, e))

    catalogdata['name'] = boxname
    catalogdata['description'] = boxdescription
    if 'versions' not in catalogdata.keys():
        catalogdata['versions'] = []

    versionmetadata = None
    for v in catalogdata['versions']:
        if boxversion == v['version']:
            versionmetadata = v
    if not versionmetadata:
        versionmetadata = {'version': boxversion, 'providers': []}
        catalogdata['versions'] += [versionmetadata]

    # Remove any existing providers with the same name, and add a new one
    if 'providers' not in versionmetadata.keys():
        versionmetadata['providers'] = []
    versionmetadata['providers'][:] = [p for p in versionmetadata['providers'] if p['name'] != providername]
    versionmetadata['providers'] += [{'name': providername, 'url': boxurl, 'checksum_type': boxchecksumtype, 'checksum': boxchecksum}]

    return json.dumps(catalogdata)


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

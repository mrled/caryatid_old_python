#!/usr/bin/env python3

# CARYATID:
# In architecture, an Atlas [https://atlas.hashicorp.com/] is a man taking the place of a column, and a Caryatid is a woman taking the place of a column

# - Receive one artifact as an argument
# - Hash it
# - Upload it to the web
# - Add it to catalog
# - Push catalog

import datetime
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
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


def addbox2catalog(boxname, boxdescription, boxversion, boxurl, boxchecksumtype, boxchecksum, catalogtext, providername):
    """Add a new Vagrant box to a catalog file

    Catalog files are one per box, with multiple versions. So there may be a catalog file for a box named "webserver", with versions 0.0.1, 0.0.2, etc.

    Arguments:
    boxname           The name of the box
    boxdescription    The description of the box
    boxurl            The URL that vagrant will fetch the box from
    boxchecksumtype   The type of checksum, such as 'sha1'
    boxchecksum       The checksum itself
    catalogtext       The text of the existing catalog, if any
    providername      The provider name, such as 'virtualbox'

    Returns:
    The text of the new catalog

    Example artifact catalog file:
    {
        "name": "testbox",
        "description": "Just an example",
        "versions": [{
            "version": "0.1.0",
            "providers": [{
                "name": "virtualbox",
                "url": "user@example.com/caryatid/boxes/testbox_0.1.0.box",
                "checksum_type": "sha1",
                "checksum": "d3597dccfdc6953d0a6eff4a9e1903f44f72ab94"
            }]
        }]
    }
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


def rfc2822date(dt=datetime.datetime.now()):
    """Convert an existing datetime.datetime object to RFC2822 format

    (This format is used by Amazon S3 REST API)

    Arguments:
    dt -- a datetime.datetime object

    Example:
        Mon, 07 Nov 2016 19:32:05 +0000
    """

    if time.localtime(time.mktime(dt.timetuple())).tm_isdst and time.daylight:
        zone = time.altzone
    else:
        zone = time.timezone

    offsethours = int(abs(zone) / 60 / 60)
    offsetminutes = int(abs(zone) / 60 % 60)
    # This next line looks wrong but it isn't - we flip the sign on purpose
    sign = '-' if zone == abs(zone) else '+'
    offset = "{}{:0>2}{:0>2}".format(sign, offsethours, offsetminutes)

    rfc2822 = datetime.datetime.strftime(dt, '%a, %d %b %Y %H:%M:%S {}'.format(offset))
    return rfc2822


def sha1sum(fp, blocksize=2**20):
    sha1 = hashlib.sha1()
    while True:
        buffer = fp.read(blocksize)
        if not buffer:
            break
        sha1.update(buffer)
    digest = sha1.hexdigest()
    return digest


def scp(file, uri):
    scpexe = 'pscp.exe' if os.name == 'nt' else 'scp'
    subprocess.check_call('{} "{}" "{}"'.format(scpexe, file, uri), shell=True)


def gettempfilename():
    tf = tempfile.mkstemp()
    name = tf[1]
    tf[0].close()
    os.unlink(name)
    return name


def addscp(name, description, version, provider, artifact, destination):
    """Upload a box to an scp server

    Arguments:
    boxname -- the name of the box
    boxdescription -- a description for our box
    boxversion -- the box version
    boxfile -- the packer artifact itself
    providername -- the name of the provider that packer generated this box for
    scpuri -- a place to copy the box to

    Note that we have made some assumptions:
    1. the catalog JSON file can be found at scpuri/boxname.json so that if
       scpuri is 'user@example.com/boxes' and boxname is 'test', we place the
       catalog JSON file at user@example.com/boxes/test.json
    2. the boxes are stored under scpuri/boxes/
    3. pscp or scp is available on the PATH
    4. you have a private key for authenticating to the scp server
    """

    artifact = resolvepath(artifact)
    boxfilename = "{}_{}_{}.box".format(name, version, provider)
    cataloguri = "{}/{}.json".format(destination, name)
    boxuri = "scp://{}/boxes/{}".format(destination, boxfilename)
    tempcatalog = gettempfilename()

    scp(artifact, boxuri)

    try:
        scp(cataloguri, tempcatalog)
        with open(artifact) as af:
            digest = sha1sum(af)
        with open(tempcatalog) as tc:
            catalogtext = tc.read()
        newcatalog = addbox2catalog(name, description, version, boxuri, 'sha1', digest, catalogtext, provider)
        with open(tempcatalog, 'rb') as tc:
            tc.write(newcatalog)
        scp(tempcatalog, cataloguri)
    finally:
        os.unlink(tempcatalog)


def addcopy(name, description, version, provider, artifact, destination):
    """Copy a file to a location on the filesystem

    name         the box name
    description  the box description
    version      the box version
    provider     the box provider
    artifact     the path to the artifact
    destination  the location of the catalog
    """
    artifact = resolvepath(artifact)
    boxfilename = "{}_{}_{}.box".format(name, version, provider)
    cataloguri = "{}/{}.json".format(destination, name)
    boxpath = resolvepath("{}/boxes/{}".format(destination, boxfilename))
    boxuri = "file:///{}".format(boxpath.replace('\\', '/'))

    os.makedirs("{}/boxes".format(destination), exist_ok=True)
    shutil.copyfile(artifact, boxpath)
    with open(artifact, 'rb') as af:
        digest = sha1sum(af)
    if os.path.exists(cataloguri):
        with open(cataloguri) as cf:
            catalogtext = cf.read()
    else:
        catalogtext = ""
    newcatalogtext = addbox2catalog(name, description, version, boxuri, 'sha1', digest, catalogtext, provider)
    with open(cataloguri, 'w') as cf:
        cf.write(newcatalogtext)

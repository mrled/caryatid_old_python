import argparse
import os
import sys

import caryatid


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

    artifact = caryatid.resolvepath(parsed.artifact)
    splart = os.path.basename(artifact).split(".")
    if splart[-1] == "box":
        boxtype = splart[-2]
        if boxtype == "virtualbox":
            pass
        else:
            raise Exception("Found a box of type '{}' but don't know how to process it".format(boxtype))
    else:
        caryatid.debugprint("Passed an artifact named '{}'; nothing to do".format(artifact))

    raise Exception("Haven't yet gotten all the arguments we need, haven't yet called any of my functions for uploading or anything")


if __name__ == '__main__':
    sys.exit(main(*sys.argv))

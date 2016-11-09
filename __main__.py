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
        "boxname",
        help="The name of the box we are building")
    parser.add_argument(
        "boxdescription",
        help="A description for the box")
    parser.add_argument(
        "boxversionbase",
        help="The version of the box")
    parser.add_argument(
        "boxfile",
        help="The artifact we are being passed")
    parser.add_argument(
        "scpuri",
        help="An SCP URI such as me@example.com/some/path. Must be a path local to the webserver that corresponds to the catalogbaseurl parameter.")

    parsed = parser.parse_args()
    if parsed.debug:
        global debug
        debug = True

    artifact = caryatid.resolvepath(parsed.artifact)
    splart = os.path.basename(artifact).split(".")
    if splart[-1] == "box":
        providername = splart[-2]
    else:
        caryatid.debugprint("Passed an artifact named '{}'; nothing to do".format(artifact))

    caryatid.newbox(
        parsed.boxname, parsed.boxdescription, parsed.boxversion,
        parsed.boxfile, providername, parsed.scpuri)


if __name__ == '__main__':
    sys.exit(main(*sys.argv))

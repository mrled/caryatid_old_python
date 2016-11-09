#!/usr/bin/env python3

# Run unit tests with "python -m unittest discover"

import json
import os
import tempfile
import unittest

import caryatid


class CaryatidIntegrationTestCase(unittest.TestCase):

    def test_addcopy(self):
        name = 'testbox'
        description = 'a test box'
        version = '0.1.0'
        provider = 'fakeprovider'

        try:
            testcatalogdir = tempfile.TemporaryDirectory()
            with tempfile.NamedTemporaryFile(suffix='.box', delete=False) as tf:
                artifact = tf.name
                tf.write(b'this is not a real box file')

            catalogpath = "{}/{}.json".format(testcatalogdir.name, name)
            boxpath = "{}/boxes/{}_{}_{}.box".format(testcatalogdir.name, name, version, provider)

            caryatid.addcopy(name, description, version, provider, artifact, testcatalogdir.name)

            if not os.path.isfile(catalogpath):
                raise Exception("JSON catalog was not created at '{}'".format(catalogpath))
            if not os.path.isfile(boxpath):
                raise Exception("Box was not copied to '{}'".format(boxpath))

            expectedjsontext = '{"description": "a test box", "name": "testbox", "versions": [{"providers": [{"checksum": "0f806a3331d5f7e282e0368ee230bd948392eeca", "checksum_type": "sha1", "name": "fakeprovider", "url": "file:///' + testcatalogdir.name.replace('\\', '/') + '/boxes/testbox_0.1.0_fakeprovider.box"}], "version": "0.1.0"}]}'
            expected = json.dumps(json.loads(expectedjsontext), sort_keys=True)
            with open(catalogpath) as cf:
                actual = json.dumps(json.load(cf), sort_keys=True)
            if actual != expected:
                raise Exception(
                    "Unexpected result:\n{}\nExpected result:\n{}\n".format(actual, expected))
        finally:
            testcatalogdir.cleanup()
            os.unlink(artifact)

            if os.path.exists(artifact):
                raise Exception("Artifact still exists at '{}'".format(artifact))
            if os.path.exists(testcatalogdir.name):
                raise Exception("Test catalog dir still exists at '{}'".format(testcatalogdir))

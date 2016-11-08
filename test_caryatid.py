#!/usr/bin/env python3

# Run unit tests with "python -m unittest discover"

import datetime
import io
import json
import unittest

import caryatid


class PackerPostprocessVagrantCatalogTestCase(unittest.TestCase):

    def _test_ab2c(self, catalogtext, expectedresult):
        value = caryatid.addbox2catalog(
            'testbox', 'a test box', '0.0.2', 'http://example.com/test.box',
            'nochecksum', 'NONE', catalogtext, 'testprovider')
        try:
            jsonvalue = json.loads(value)
        except Exception as e:
            raise Exception("Could not load JSON for {} because {}".format(value, e))
        jsonshouldbe = json.loads(expectedresult)
        if jsonvalue != jsonshouldbe:
            raise Exception("Catalog value was not set properly\n\nINPUT CATALOG:\n{}\nOUTPUT CATALOG:\n{}\n\nSHOULD BE:\n{}\n\n".format(catalogtext, value, jsonshouldbe))

    def test_ab2c_with_existing_catalog_one_version_no_providers(self):
        catalog = '{"name": "testbox", "versions": [{"version": "0.0.2"}], "description": "a test box"}'
        shouldbe = '{"name": "testbox", "versions": [{"version": "0.0.2", "providers": [{"name": "testprovider", "checksum": "NONE", "checksum_type": "nochecksum", "url": "http://example.com/test.box"}]}], "description": "a test box"}'
        self._test_ab2c(catalog, shouldbe)

    def test_ab2c_with_existing_catalog_one_version_different_provider_same_data(self):
        catalog = '{"name": "testbox", "versions": [{"version": "0.0.1", "providers": [{"name": "testprovider", "checksum": "NONE", "checksum_type": "nochecksum", "url": "http://example.com/test.box"}]}], "description": "a test box"}'
        shouldbe = '{"name": "testbox", "versions": [{"version": "0.0.1", "providers": [{"name": "testprovider", "checksum": "NONE", "checksum_type": "nochecksum", "url": "http://example.com/test.box"}]}, {"version": "0.0.2", "providers": [{"name": "testprovider", "checksum": "NONE", "checksum_type": "nochecksum", "url": "http://example.com/test.box"}]}], "description": "a test box"}'
        self._test_ab2c(catalog, shouldbe)

    def test_ab2c_with_existing_catalog_one_version_same_provider_same_name_different_data(self):
        catalog = '{"name": "testbox", "versions": [{"version": "0.0.2", "providers": [{"name": "testprovider", "checksum": "EXISTINGSUM", "checksum_type": "sometype", "url": "http://ANOTHERHOST.example.com/test.box"}]}], "description": "a test box"}'
        shouldbe = '{"name": "testbox", "versions": [{"version": "0.0.2", "providers": [{"name": "testprovider", "checksum": "NONE", "checksum_type": "nochecksum", "url": "http://example.com/test.box"}]}], "description": "a test box"}'
        self._test_ab2c(catalog, shouldbe)

    def test_ab2c_with_empty_catalogs(self):
        testcatalogs = ['', '{}', '{"name": "testbox", "description": "a test box"}']
        expectedresult = '{"name": "testbox", "versions": [{"version": "0.0.2", "providers": [{"name": "testprovider", "checksum": "NONE", "checksum_type": "nochecksum", "url": "http://example.com/test.box"}]}], "description": "a test box"}'
        for catalog in testcatalogs:
            self._test_ab2c(catalog, expectedresult)

    def test_rfc2822time(self):
        indatestr = '2015-02-02-18-31-29 -0600'
        indatefmt = '%Y-%m-%d-%H-%M-%S %z'
        expectedresult = "Mon, 02 Feb 2015 18:31:29 -0600"
        testdate = datetime.datetime.strptime(indatestr, indatefmt)
        actualresult = caryatid.rfc2822date(testdate)
        if actualresult != expectedresult:
            raise Exception("Failed to encode rfc2822 time correctly. Input/Expected/Actual:\n'{}'\n'{}'\n'{}'\n".format(indatestr, expectedresult, actualresult))

    def test_sha1sum(self):
        data = b'thought leader / thot follower'
        fp = io.BytesIO(data)
        expected = '7dec495be4b03cf87189582a94477b05c1eb6236'
        result = caryatid.sha1sum(fp)
        if result != expected:
            raise Exception("Failed to calculate sha1sum correctly. Input/Expected/Actual:\n{}\n{}\n{}\n".format(data, expected, result))

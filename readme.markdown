# Caryatid

An [Atlas](https://atlas.hashicorp.com) is ["a support sculpted in the form of a man"](https://en.wikipedia.org/wiki/Atlas_(architecture)); a [Caryatid](https://github.com/mrled/caryatid) is such a support in the form of a [woman](https://en.wikipedia.org/wiki/Caryatid).

Caryatid is a minimal alternative to Atlas. It can build Vagrant catalogs and copy files to local or remote storage, and it can be invoked as a Packer post-processor.

More specifically, Caryatid intended as a way to host a (versioned) Vagrant catalog on systems without having to use (and pay for) Atlas, and without having to trust a third party if you don't want to. It's designed to work with dumb remote servers - all you need to have a remote scp catalog for example is a standard scp server, no server-side logic required. It supports multiple storage backends. For now, these are just scp and file backends; we would like to add support for more backends in the future (so long as they require no server-side logic).

Note that the file backend is useful even if the fileserver is local, because Vagrant needs the JSON catalog to be able to use versioned boxes. That is, using Caryatid to manage a JSON catalog of box versions is an improvement over running packer and then just doing a `vagrant box add` on the resulting box, because this way Vagrant can see when your box has a new version.

## Prerequisites

- Python3
- OpenSSH's `scp` on Unix or PuTTY's `pscp.exe` on Windows to use the scp backend
- Disk space to keep (large) Vagrant box files
- Vagrant box files (I generate mine using `packer`)

## Invoking from the command line

    python -m caryatid -h

## Invoking tests

Unit tests: 

    python -m unittest discover

Integration tests (slow!):

    python -m unittest discover --pattern "integrationtest*.py"

## Invoking from packer

To invoke from packer, add a shell-local post-processor:

    {
      "type": "shell-local",
      "inline": ["python -m /path/to/caryatid/ add boxname description version provider artifact copy /somewhere/vagrant/"]
    }

## Output and directory structure

Caryatid uses the same structure, no matter which backend you use. For instance, calling Caryatid like this:

    caryatid add testbox "a box for testing" 1.0.0 virtualbox somefile.box copy /srv/vagrant

Will result in a directory structure that looks like this (note that we rename the box itself):

    /srv/vagrant
        /testbox.json: the JSON catalog
        /boxes
            /testbox_1.0.0_virtualbox.box: the large VM box file itself

And the `testbox.json` catalog will look like this:

    {
        "name": "testbox",
        "description": "a box for testing",
        "versions": [{
            "version": "1.0.0",
            "providers": [{
                "name": "virtualbox",
                "url": "file:///srv/vagrant/boxes/testbox_1.0.0.box",
                "checksum_type": "sha1",
                "checksum": "d3597dccfdc6953d0a6eff4a9e1903f44f72ab94"
            }]
        }]
    }

This can be consumed in a Vagrant file by using the JSON catalog as the box URL in a `Vagrantfile`:

    config.vm.box_url = "file:///srv/vagrant/testbox.json"

## Caveats

- Vagrant is [supposed to support scp](https://github.com/mitchellh/vagrant/pull/1041), but [apparently doesn't bundle a properly-built `curl` yet](https://github.com/mitchellh/vagrant-installers/issues/30). This means you may need to build your own `curl` that supports scp, and possibly even replace your system-supplied curl with that one, in order to use catalogs hosted on scp with Vagrant. (Note that we do not rely on curl, so even if your curl is old, Caryatid can still push to scp backends.)

## Roadmap / wishlist

- Would love to support S3 storage, however, there isn't a way to authenticate to S3 through Vagrant, at least without third party libraries. This would mean that the boxes stored on S3 would be public. This is fine for my use case, except that it means anyone with the URL to a box could cost me money just by downloading the boxes over and over
- Some sort of webserver mode would be nice, and is in line with the no server-side logic goal. Probably require an scp url for doing uploads in addition to an http url for vagrant to fetch the boxes?

## See also

- [How to set up a self-hosted "vagrant cloud" with versioned, self-packaged vagrant boxes](https://github.com/hollodotme/Helpers/blob/master/Tutorials/vagrant/self-hosted-vagrant-boxes-with-versioning.md)
- [Distributing Vagrant base boxes securely](http://chase-seibert.github.io/blog/2014/05/18/vagrant-authenticated-private-box-urls.html)


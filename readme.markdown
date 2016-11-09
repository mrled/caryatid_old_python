# Caryatid

An [Atlas](https://atlas.hashicorp.com) is ["a support sculpted in the form of a man"](https://en.wikipedia.org/wiki/Atlas_(architecture)); a [Caryatid](https://github.com/mrled/caryatid) is such a support in the form of a [woman](https://en.wikipedia.org/wiki/Caryatid).

More specifically, this is intended as a way to host Vagrant boxes on remote systems without having to use (and pay for) Atlas, and without having to trust a third party if you don't want to. It's also designed to work with dumb remote servers - all you need to have a remote scp catalog for example is a standard scp server, no server-side logic required.

Caryatid can build Vagrant catalogs and upload files to remote storage, and it can be invoked as a Packer post-processor.

## Caveats

- Vagrant is [supposed to support scp](https://github.com/mitchellh/vagrant/pull/1041), but [apparently doesn't bundle a properly-built `curl` yet](https://github.com/mitchellh/vagrant-installers/issues/30). This means you may need to build your own `curl` that supports scp, and possibly even replace your system-supplied curl with that one.


## Roadmap / wishlist

- Would love to support S3 storage, however, there isn't a way to authenticate to S3 through Vagrant without third party libraries. This would mean that the boxes stored on S3 would be public. This is fine for my use case, except that it means anyone with the URL to a box could cost me money just by downloading the boxes over and over
- Some sort of webserver mode would be nice, and is in line with the no server-side logic goal. Probably require an scp url for doing uploads in addition to an http url for vagrant to fetch the boxes?
- Likewise, some sort of fileserver mode would be useful too. Even if it's all local development, this would give an advantage over doing `vagrant box add` on the raw `.box` file - versioning. Vagrant doesn't keep track of box versions when doing `vagrant box add` but it will do so if pointed to a catalog.

## Invoking from packer

Add a shell-local post-processor:

    {
      "type": "shell-local",
      "inline": ["../../scripts/caryatid/__main__.py {{user `boxname`}} {{user `description`}} {{user `version`}} {{user `output_path`}} {{user `scpuri`}}"]
    }

## See also

- [How to set up a self-hosted "vagrant cloud" with versioned, self-packaged vagrant boxes](https://github.com/hollodotme/Helpers/blob/master/Tutorials/vagrant/self-hosted-vagrant-boxes-with-versioning.md)
- [Distributing Vagrant base boxes securely](http://chase-seibert.github.io/blog/2014/05/18/vagrant-authenticated-private-box-urls.html)
==================================================================================
replaylib - Make better tests when using remote HTTP services
==================================================================================

:Authors:
    Scott Torborg (storborg)
    Mike Spindel (deactivated)
:Version: 0.1

This (very experimental) library allows you to install replacement stubs
for httplib methods which record interactions with remote servers, and then
play them back. Because urllib depends on httplib functionality, replaylib
will record and play back urllib interactions as well.

It is intended to allow streamlined tests for services which interact with
remote services: e.g. payment processors, shipping APIs, etc. To use it, just:

1. Run your test suite while recording with replaylib.
2. On subsequent runs, play back from replaylib. Tests will run faster, and
   won't require external services.

It is fully tested, with 100% line and branch coverage, and works well with all
APIs we have tried it on "in the wild".

*Note* Use at your own risk!

Installation
============

Simple as::

    $ easy_install replaylib

Or if you prefer, download the source and then::

    $ python setup.py build
    $ python setup.py install

Example
=======

>>> import replaylib
>>> import urllib

>>> replaylib.start_record()
# Do some stuff with urllib.
>>> urllib.urlopen('http://www.google.com')
>>> replaylib.stop_record('activity.pkl')

>>> replaylib.start_playback('activity.pkl')
# Won't actually make a request to google.com
>>> urllib.urlopen('http://www.google.com')
>>> replaylib.stop_playback()

Nose Plugin
===========

ReplayLib also comes with a nose plugin to make recording and playing back the
interactions used by your test suites even simpler::

    $ nosetests --replaylib-record=test.pkl
    $ nosetests --replaylib-playback=test.pkl


License
=======

ReplayLib is released under the GNU General Public License (GPL). See the
LICENSE file for full text of the license.


.. # vim: syntax=rst expandtab tabstop=4 shiftwidth=4 shiftround

==================================================================================
replaylib - Make better tests when using remote services
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
remote services: e.g. payment processors, shipping APIs, etc.

*Note* Use at your own risk!

Installation
============

Simple as::

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


.. # vim: syntax=rst expandtab tabstop=4 shiftwidth=4 shiftround

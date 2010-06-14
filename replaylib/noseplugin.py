import logging
import os
import replaylib
from nose.plugins import Plugin

log = logging.getLogger(__name__)


class ReplayLibPlugin(Plugin):
    enabled = False
    name = "replaylib"
    
    def options(self, parser, env=os.environ):
        "Add options to nosetests."
        parser.add_option("--%s-record" % self.name,
                          action="store",
                          metavar="FILE",
                          dest="record_filename",
                          help="Record actions to this file.")
        parser.add_option("--%s-playback" % self.name,
                          action="store",
                          metavar="FILE",
                          dest="playback_filename",
                          help="Playback actions from this file.")

    def configure(self, options, config):
        Plugin.configure(self, options, config)
        if options.record_filename and options.playback_filename:
            self.enabled = False
            log.error("Cannot record and playback at the same time. "
                      "Replaylib will not be enabled.")
            return
        self.enabled = True
        self.record_filename = options.record_filename
        self.playback_filename = options.playback_filename

    def begin(self):
        if self.record_filename:
            replaylib.start_record()
        elif self.playback_filename:
            replaylib.start_playback(self.playback_filename)

    def report(self, stream):
        if self.record_filename:
            replaylib.stop_record(self.record_filename)
        elif self.playback_filename:
            replaylib.stop_playback()

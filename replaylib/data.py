from collections import defaultdict

"""
Replay maps will be stored as a pickled dict that looks like:

    {'<sha1 of canonicalized request data>': ['first response body',
                                              'second response body',
                                              'third response body',
                                              ...],
     '<sha1 of different request data>': ['first response body',
                                          'second response body']}
"""


class ReplayDataResponse(object):

    def __init__(self):
        self.body_chunks = []

    def rec_start(self, version, status, reason, headers):
        self.version = version
        self.status = status
        self.reason = reason
        self.headers = headers

    def rec_body(self, s):
        self.body_chunks.append(s)

    @property
    def body(self):
        return "".join(self.body_chunks)


class ReplayData(object):

    def __init__(self):
        self.map = defaultdict(list)
        self.playback_pos = defaultdict(int)

    def start_response(self, hash):
        resp = ReplayDataResponse()
        self.map[hash].append(resp)
        return resp

    def get_next_response(self, hash):
        pos = self.playback_pos[hash]
        response = self.map[hash][pos]
        self.playback_pos[hash] += 1
        return response

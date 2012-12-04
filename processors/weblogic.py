import re

class WeblogicFilter(object):
    def __init__(self, line_format):
        self.line_format = line_format
        re1 = '<([^>]*)>#*<([^>]+)> <(\w+)> <(\w+)> <([^>]+)> <(\w+)> <([^>]+)> <<([^>]+)>> <(\S*)> <(\S*)> <([^>]+)> <([^>]+)> <([^>]+)>'
        # re1_old = '.?<([^>]+)> <(\w+)> <(\w+)> <([^>]+)> <(\w+)> <([^>]+)> <<([^>]+)>> <(\S*)> <(\S*)> <([^>]+)> <([^>]+)> <([^>]+)>'
        self.logpat   = re.compile(re1)

    def _wl_log(self, lines):
        log = ''

        groups = (self.logpat.search(line) for line in lines)
        tuples = (g.groups() for g in groups if g)
        colnames = ('filename', 'timestamp', 'severity', 'subsystem', 'machine', 'server', 'thread_id', 'user_id', 'transaction_id', 'diag_ctx_id', 'raw_time', 'bea_id', 'message')

        log = (dict(zip(colnames, t)) for t in tuples)

        return log

    def processor(self, lines):
        for line in self._wl_log(lines):
            print line
            yield self.line_format.format(**line)

def get_instance(*args, **kwargs):
    return WeblogicFilter(*args, **kwargs)

import sys

class stderrTransport(object):
    def __init__(self, *args, **kwargs):
        pass

    def send(self, line, logfile='', logtype='', tags='', fields=''):
        sys.stderr.write(line + '\n')

def get_instance(*args, **kwargs):
    return stderrTransport(*args, **kwargs)


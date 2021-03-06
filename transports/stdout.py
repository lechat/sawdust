import sys

class stdoutTransport(object):
    def __init__(self, *args, **kwargs):
        pass

    def send(self, line, logfile='', logtype='', tags='', fields=''):
        sys.stdout.write(line + '\n')

def get_instance(*args, **kwargs):
    return stdoutTransport(*args, **kwargs)

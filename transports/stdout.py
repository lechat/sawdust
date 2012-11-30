class stdoutTransport(object):
    def send(self, line):
        print line

def get_instance(*args, **kwargs):
    return stdoutTransport(*args, **kwargs)

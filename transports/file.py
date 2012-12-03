class fileTransport(object):
    def __init__(self, file_name):
        self.file_name = file_name

    def send(self, line, logfile='', logtype='', tags='', fields=''):
        with open(self.file_name, 'a') as out:
            out.write(line + '\n')

def get_instance(*args, **kwargs):
    return fileTransport(*args, **kwargs)


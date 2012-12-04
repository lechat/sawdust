import re

class PassthroughFilter(object):
    def __init__(self, line_format):
        self.line_format = line_format

    def processor(self, lines):
        for line in lines:
            yield line

def get_instance(*args, **kwargs):
    return PassthroughFilter(*args, **kwargs)

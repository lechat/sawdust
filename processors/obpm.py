import sys
import time

class ObpmFilter(object):
    def __init__(self, lines, line_format):
        self.lines = lines
        self.line_format = line_format

    def _obpm_log(self, lines):
        line_param = {'message': ''}
        # <D>, "Nov 6, 2012 3:48:32 PM", Engine, Main, <12> [ACTIVE] ExecuteThre, "Activity '/CSPSProcess#Default-6.1/LogOutException[CheckSpaceAvailability]' is receiving instance '/CSPSProcess#Default-6.1/10811/0'."

        #0         1         2         3         4         5         6         7
        #01234567890123456789012345678901234567890123456789012345678901234567890123
        #0001Engine         Main      <12> [ACTIVE] ExecuteThre000120121106T154832
        #-001Activity '/CSPSProcess\#Default-6.1/LogOutException[CheckSpaceAvailab
        #-002ility]' is receiving instance '/CSPSProcess\#Default-6.1/10811/0'.
        #-003
        try:
            for line in lines:
                line = line.strip()
                if line.startswith('00'):
                    if line_param['message']:
                        yield line_param
                        line_param = {}

                    severity = line[54:58]
                    if severity == '0001':
                        line_param['severity'] = 'D'
                        line_param['long_severity'] = 'Debug'
                    elif severity == '0101':
                        line_param['severity'] = 'I'
                        line_param['long_severity'] = 'Info'
                    else:
                        print >> sys.stderr, line
                        line_param['severity'] = '<U>'

                    line_param['engine'] = line[4:19].strip()
                    line_param['main'] = line[19:29].strip()
                    line_param['thread'] = line[29:54]
                    line_param['timestamp'] = time.strftime('%b %d, %Y %H:%M:%S', time.strptime(line[58:73], '%Y%m%dT%H%M%S'))
                    line_param['message'] = ''
                else:
                    line_param['message'] += line[4:]
        except KeyError:
            print >> sys.stderr, 'ERROR: Invalid OBPM log line "%s"' % line
            sys.exit(200)

    def processor(self, lines):
        for line in self._obpm_log(lines):
            yield self.line_format.format(**line)

def get_instance(*args, **kwargs):
    return ObpmFilter(*args, **kwargs)

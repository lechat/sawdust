# sawdust.py
#
# Process an log file(s)
import re
import os
import fnmatch
import sys
import time

re1 = '<([^>]*)>#*<([^>]+)> <(\w+)> <(\w+)> <([^>]+)> <(\w+)> <([^>]+)> <<([^>]+)>> <(\S*)> <(\S*)> <([^>]+)> <([^>]+)> <([^>]+)>'
re1_old = '.?<([^>]+)> <(\w+)> <(\w+)> <([^>]+)> <(\w+)> <([^>]+)> <<([^>]+)>> <(\S*)> <(\S*)> <([^>]+)> <([^>]+)> <([^>]+)>'

logpat   = re.compile(re1)

def gen_find(filepat, top):
    for path, _, filelist in os.walk(top):
        for name in fnmatch.filter(filelist, filepat):
            yield os.path.join(path, name)

def gen_cat(sources):
    for s in sources:
        for item in s:
            yield '%s' % (item)

def gen_open(filenames):
    for name in filenames:
        if name:
            yield open(name)
        else:
            yield sys.stdin

def gen_grep(pat, lines):
    patc = re.compile(pat)
    for line in lines:
        if patc.search(line):
            yield line

def gen_line_find(what, lines):
    for line in lines:
        if line.find(what) > -1:
            yield line

def lines_from_dir(filepat, dirname=None):
    if dirname:
        names = gen_find(filepat, dirname)
    else:
        names = [filepat]
    files = gen_open(names)
    file_lines = gen_cat(files)
    return file_lines

def obpm_log(lines, format_str='{severity}, "{timestamp}", {engine}, {main}, {thread}, "{message}"'):
    full_line = ''
    print_next_line = False
    line_param = {}
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
                if full_line != '':
                    if print_next_line:
                        print >> sys.stderr, full_line
                        print full_line
                        print_next_line = False
                    # print full_line
                    # log.append(full_line)
                    yield full_line
                    full_line = ''
                    line_param = {}

                severity = line[54:58]
                if severity == '0001':
                    line_param['severity'] = 'D'
                    line_param['long_severity'] = 'Debug'
                elif severity == '0101':
                    line_param['severity'] = 'I'
                    line_param['long_severity'] = 'Info'
                else:
                    print_next_line = True
                    print >> sys.stderr, line
                    line_param['severity'] = '<U>'

                line_param['engine'] = line[4:19].strip()
                line_param['main'] = line[19:29].strip()
                line_param['thread'] = line[29:54]
                line_param['timestamp'] = time.strftime('%b %d, %Y %H:%M:%S', time.strptime(line[58:73], '%Y%m%dT%H%M%S'))
                line_param['message'] = ''
                full_line = (format_str).format(**line_param)
            else:
                line_param['message'] += line[4:]
                full_line = (format_str).format(**line_param)
    except KeyError:
        print >> sys.stderr, 'ERROR: Invalid OBPM log line "%s"' % line
        sys.exit(200)

def wl_log(lines):
    log = ''

    groups = (logpat.search(line) for line in lines)
    tuples = (g.groups() for g in groups if g)
    colnames = ('filename', 'timestamp', 'severity', 'subsystem', 'machine', 'server', 'thread_id', 'user_id', 'transaction_id', 'diag_ctx_id', 'raw_time', 'bea_id', 'message')

    log = (dict(zip(colnames, t)) for t in tuples)

    return log

def read_prop_file(properties_file):
    properties = {}
    pp = open(properties_file, 'r')
    for line in pp:
        l = line.split('=')
        if len(l) > 1:
            key = l[0].strip()
            value = '='.join(l[1:]).strip()
            properties[key] = value

    pp.close()
    return properties

def follow(thefilename):

    if thefilename:
        ino = 0
        while True:
            with open(thefilename, 'r') as thefile:
                thefile.seek(0, 2)
                while True:
                    line = thefile.readline()
                    if not line:
                        time.sleep(0.1)
                        # Check of file has been rotated
                        new_ino = os.stat(thefilename).st_ino
                        if ino != new_ino:
                            # File has been rotated - read new file
                            ino = new_ino
                            break
                        continue

                    yield line

    else:
        with sys.stdin as thefile:
            while True:
                line = thefile.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                yield line

def follow_stdin():
    with sys.stdin as thefile:
        while True:
            line = thefile.readline()
            if not line:
                break
            yield line

class StdoutTransport():
    def send(self, line):
        print line


def transport_resolver(which_transport):
    if which_transport == None or which_transport == 'stdout':
        return StdoutTransport()
    else:
        print 'ERROR: Transport "%s" is not supported' % which_transport
        return None

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser('obpm_logs.py')
    parser.add_argument('--pattern', dest='fmt', required=False, help='Format string for output. Available parameters to output are: {severity}, {long_severity}, {engine}, {thread}, {main}, {timestamp}, {message}')
    parser.add_argument('-f', '--follow', action='store_true', dest='follow', required=False, help='Follow file like tail -f')
    parser.add_argument('-p', '--processor', dest='filter', choices=['obpm'], type=str, default='obpm', required=False, help='Log line filter')

    parser.add_argument('logfile', nargs='?', help="OBPM Engine log file to read. If not specified - it will be read from STDIN")
    parser.add_argument('transport', nargs='?', help='Send log lines to specified transport. It it is omitted - send to stdout')

    args = parser.parse_args()

    transport = transport_resolver(args.transport)
    if not transport:
        sys.exit(201)

    if args.follow:
        lines = follow(args.logfile)
    else:
        if args.logfile:
            lines = lines_from_dir(args.logfile)
        else:
            lines = follow_stdin()

    if args.filter:
        if args.filter == 'obpm':
            log = obpm_log(lines, args.fmt if args.fmt else '<{severity}>, "{timestamp}", {engine}, {main}, {thread}, "{message}"')
    else:
        log = lines

    for dust in log:
        transport.send(dust)



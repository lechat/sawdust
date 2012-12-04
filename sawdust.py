# sawdust.py
#
# Process an log file(s)
import os
import os.path
import fnmatch
import pprint
import sys
import re
import time

def import_file(path_to_module):
    """Note: path to module must be a relative path starting from a directory in sys.path"""
    module_dir, module_file = os.path.split(path_to_module)
    module_name, _module_ext = os.path.splitext(module_file)
    module_package = ".".join(module_dir.split(os.path.sep)) + '.' + module_name

    module_obj = __import__(module_package, fromlist=['*'])
    module_obj.__file__ = path_to_module
    return module_obj

def gen_find(filepat, top):
    for path, _, filelist in os.walk(top):
        for name in fnmatch.processor(filelist, filepat):
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


def class_factory(class_type, which_class, *args, **kwargs):
    class_instance = None
    # try:
    class_instance = import_file(class_type + '/' + which_class).get_instance(*args, **kwargs)
    # except ImportError:
    #     print '%s "%s" is not found' % (class_type, which_class)
    #     sys.exit(1)

    return class_instance

def transport_resolver(which_transport, *args, **kwargs):
    if which_transport == None:
        which_transport = 'stdout'

    return class_factory('transports', which_transport, *args, **kwargs)

def processor_resolver(which_processor, *args, **kwargs):
    return class_factory('processors', which_processor, *args, **kwargs)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser('sawdust.py')
    parser.add_argument('-t', '--pattern', dest='fmt', required=False, help='Format string for output. Available parameters to output are: {severity}, {long_severity}, {engine}, {thread}, {main}, {timestamp}, {message}')
    parser.add_argument('-f', '--follow', action='store_true', dest='follow', required=False, help='Follow file like tail -f')
    parser.add_argument('-p', '--processor', dest='processor', choices=['obpm', 'weblogic'], type=str, default='obpm', required=False, help='Log line processor')
    parser.add_argument('-c', '--config', dest='config_path', type=str, required=False, help='Path to sawdust configuration file')
    parser.add_argument('-v', '--verbose', dest='verbose', type=bool, required=False, help='Be verbose')

    parser.add_argument('logfile', nargs='?', help="OBPM Engine log file to read. If not specified - it will be read from STDIN")
    parser.add_argument('transport', nargs='?', help='Send log lines to specified transport. It it is omitted - send to stdout')

    arguments = parser.parse_args()

    logfiles = {}
    if arguments.config_path:
        cfg_list = import_file(arguments.config_path).config
        for logfile_config in cfg_list:
            for logfile in logfile_config['filenames']:
                log_item = logfiles.setdefault(logfile, {})
                log_item['follow'] = logfile_config['follow']
                log_item['type'] = logfile_config['type']
                log_item['tags'] = logfile_config['tags']
                for transport in logfile_config['transports']:
                    log_item.setdefault('transports', {})
                    if transport[0] in log_item['transports'].keys():
                        print 'WARNING: Transport "%s" defined more than once for "%s" file(s). Skipping' % (transport[0], logfile)
                        continue
                    log_item['transports'][transport[0]] = transport_resolver(transport[0], *transport[1:])
                for processor in logfile_config['processors']:
                    log_item.setdefault('processors', {})
                    if processor[0] in log_item['processors'].keys():
                        print 'WARNING: Processor "%s" defined more than once for "%s" file(s). Skipping' % (processor[0], logfile)
                        continue
                    log_item['processors'][processor[0]] = processor_resolver(processor[0], *processor[1:])

# TODO: add tags

    if not logfiles:
        logfiles[arguments.logfile] = {}
        logfiles[arguments.logfile]['follow'] = arguments.follow
        logfiles[arguments.logfile]['transports'] = [transport_resolver(arguments.transport)]
        logfiles[arguments.logfile]['processors'] = [processor_resolver(arguments.processor, arguments.fmt if arguments.fmt else '<{severity}>, "{timestamp}", {engine}, {main}, {thread}, "{message}"')]

    if arguments.verbose:
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(logfiles)

    for logfile, logparams in logfiles.iteritems():
        if logfile == 'stdin':
            lines = follow_stdin()
        else:
            if logparams['follow']:
                lines = follow(logfile)
            else:
                lines = lines_from_dir(logfile)

        for processor in logparams['processors'].values():
            for dust in processor.processor(lines):
                for transport in logparams['transports'].values():
                    transport.send(dust, logfile=logfile, logtype=logparams['type'], tags=logparams['tags'])



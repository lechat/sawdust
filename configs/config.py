config = [
    {
        'filenames': ['/home/xleap/gen/CSPS_EDU_BPM_ENG.log.1'],
        'follow': False,
        'type': 'obpm-log',
        'transports': [('stdout', ), ('redis_t', 'redis://10.3.76.15:6379/0', 'logstash:obpm')],
        # 'transports': [('file', '/tmp/outfile'), ('redis_t', )],
        'processors': [('obpm', '<{severity}>, "{timestamp}", {engine}, {main}, {thread}, "{message}"')],
        'tags': ['csps', 'edu', 'bpm', 'obpme1']
    },
    # {
    #     'filenames': ['/home/xleap/gen/CSPS_EDU_BPM_ENG.log.1'],
    #     'follow': False,
    #     'transports': [('stderr', ), ('file', '/tmp/outfile')],
    #     # 'transports': [('file', '/tmp/outfile'), ('redis_t', )],
    #     'processors': [('obpm', '<{severity}>, "{timestamp}", {engine}, {main}, {thread}, "{message}"')]
    # }
]

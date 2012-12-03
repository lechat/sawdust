import datetime
import json
import redis
import socket
import urlparse

class RedisTransport(object):

    def __init__(self, redis_url, redis_namespace):
        if not redis_url:
            redis_url = 'redis://localhost:6379/0'

        if not redis_namespace:
            redis_namespace = 'logstash:sawdust'

        _url = urlparse.urlparse(redis_url, scheme="redis")
        _, _, _db = _url.path.rpartition("/")

        self.redis = redis.StrictRedis(host=_url.hostname, port=_url.port, db=int(_db), socket_timeout=10)
        self.redis_namespace = redis_namespace
        self.current_host = socket.gethostname()

    def send(self, line, logfile='', logtype='file', tags=[], fields={}):
        timestamp = datetime.datetime.utcnow().isoformat()
        msg = json.dumps({
            '@source': logfile,
            '@type': logtype,
            '@tags': tags,
            '@fields': fields,
            '@timestamp': timestamp,
            '@source_host': self.current_host,
            '@source_path': logfile,
            '@message': line,
        })

        self.redis.rpush(self.redis_namespace, msg)

def get_instance(*args, **kwargs):
    return RedisTransport(*args, **kwargs)


import redis

from config import config
from app import FileTransferApp
from storage import FileSystemStorageDriver

import logging

s = None

def check_config():
    if not 'redis_host' in config:
        config['redis_host'] = 'localhost'
    if not 'redis_port' in config:
        config['redis_port'] = '6379'
    if not 'storage_driver' in config:
        config['storage_driver'] = FileSystemStorageDriver

    global s
    try:
        s = config['storage_driver'](config)
    except Exception as e:
        logging.error(e)
        logging.error('Failed to create storage driver')
        logging.error('Exiting...')
        exit(2)

    for k in s.required_config():
        if not k in config:
            config[k] = s.required_config()[k]
    
def message_handler(msg):
    data = str(msg['data'], 'utf-8')
    if msg is not None and msg.get('type') == 'pmessage':
        if not data.endswith('-t') and not data.endswith('-l'):
            s.delete(data)

check_config()

try:
    r = redis.Redis(host=config['redis_host'], port=config['redis_port'], db=0)
except:
    logging.error('Could not connect to redis database')
    logging.error('Exiting...')
    exit(2)

r.config_set('notify-keyspace-events', 'KEA')
sub = r.pubsub()
sub.psubscribe(**{'__keyevent@0__:expired': message_handler})

sub.run_in_thread(sleep_time=0.01)

app = FileTransferApp(r, s)
app.start();
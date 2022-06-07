import redis

from config import config
from app import FileTransferApp
from storage import FileSystemStorageDriver

s = FileSystemStorageDriver()

def check_config():
    if not 'file_location' in config:
        config['file_location'] = 'files'
    if not 'redis_host' in config:
        config['redis_host'] = 'localhost'
    if not 'redis_port' in config:
        config['redi_port'] = '6379'
    
def message_handler(msg):
    data = str(msg['data'], 'utf-8')
    if msg is not None and msg.get('type') == 'pmessage':
        if not data.endswith('-t') and not data.endswith('-l'):
            s.delete(data)
            # os.remove(os.path.join(config['file_location'], data))

check_config()

r = redis.Redis(host=config['redis_host'], port=config['redis_port'], db=0)

r.config_set('notify-keyspace-events', 'KEA')
sub = r.pubsub()
sub.psubscribe(**{'__keyevent@0__:expired': message_handler})

sub.run_in_thread(sleep_time=0.01)

app = FileTransferApp(r, FileSystemStorageDriver())
app.start();
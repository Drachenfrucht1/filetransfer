from bottle import template, request, static_file, abort, Bottle, parse_range_header, _file_iter_range, HTTPResponse, HTTPError
import redis

from random import random
from datetime import datetime


import storage

from config import config

app = Bottle()

class FileTransferApp():
    r = None
    app = Bottle()
    storage: storage.StorageDriver
    def __init__(self, redis: redis.Redis, s: storage.StorageDriver):
        storage = s
        self.r = redis

        @self.app.get('/')
        def index_handler():
            return static_file('index.html', root='./views');

        @self.app.get('/f/<id>')
        def file_handler(id):
            file_name = self.r.get(id)
            if file_name != None:
                return template('file.html', f=file_name, id=id);
            return abort(404, 'File does not exist!');

        @self.app.post('/u')
        def upload_handler():
            f = request.files.get('file')
            h = hash(datetime.now().timestamp()+random())
            # get a new hash that is not currently in use
            while self.r.set(h, f.filename, ex=10*60, nx=True) == None:
                h = hash(datetime.now().timestamp()+random())

            # set additional attributes
            self.r.set(str(h) + '-t', f.content_type, ex=10*60+10)
            self.r.set(str(h) + '-l', f.content_length, ex=10*60+10)

            # f.save(os.path.join(config['file_location'],str(h)), overwrite=True)
            storage.store(str(h), f.file)
            return template('{{hash_value}}', hash_value=str(h))
        
        @self.app.get('/f/d/<id>')
        def file_download_handler(id):
            file_name = self.r.get(id);
            if file_name != None:
                # see  static_file source code (just returning the file threw encoding errors)
                headers = dict()
                headers['Content-Disposition'] = 'attachment; filename="' + str(file_name, 'utf-8') +'"'
                headers['Content-Type'] = self.r.get(id + '-t')
                headers['Content-Length'] = clen = self.r.get(id + '-l')

                body = storage.get(id)

                headers["Accept-Ranges"] = "bytes"
                ranges = request.environ.get('HTTP_RANGE')
                if 'HTTP_RANGE' in request.environ:
                    ranges = list(parse_range_header(request.environ['HTTP_RANGE'], clen))
                    if not ranges:
                        return HTTPError(416, "Requested Range Not Satisfiable")
                    offset, end = ranges[0]
                    headers["Content-Range"] = "bytes %d-%d/%d" % (offset, end-1, clen)
                    headers["Content-Length"] = str(end-offset)
                    if body: body = _file_iter_range(body, offset, end-offset)
                    return HTTPResponse(body, status=206, **headers)
                return HTTPResponse(body, **headers)


                # return storage.get(id)
                # return static_file(id, root=config['file_location'], mimetype=self.r.get(id + '-t'), download=str(file_name, 'utf-8'))
            return abort(404, 'File does not exist!');
            
        @self.app.get('/static/<filename>')
        def static_handler(filename):
            return static_file(filename, root='./static');

        @self.app.get('/webfonts/<filename>')
        def webfonts_handler(filename):
            return static_file(filename, root='./static/webfonts');

        @self.app.get('/about')
        def about_page():
            return static_file('about.html', root='./views')

        @self.app.error(404)
        def error404( error):
            return static_file('404.html', root='./views')

    def start(self):
        # cherrypy.tree.graft(self.app, '/')
        # cherrypy.server.unsubscribe()
        # server = cherrypy._cpserver.Server()

        # server.socket_host = '0.0.0.0'
        # server.socket_port = 8080
        # server.thread_pool_max = 30

        # server.subscribe()

        # cherrypy.engine.start()
        # cherrypy.engine.block()

        self.app.run()

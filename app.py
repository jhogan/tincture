import json
import sys
from functools import reduce
import pdb; B=pdb.set_trace
from pprint import pprint

class application:

    @property
    def environment(self):
        return self._env 

    def __call__(self, env, sres):
        
        self._env = env
        
        try:
            try:
                reqsize = int(self.environment.get('CONTENT_LENGTH', 0))
            except(ValueError):
                reqsize = 0

            reqbody = self.environment['wsgi.input'].read(reqsize).decode('utf-8')

            if len(reqbody) == 0:
                raise http400('No data in post')
                
            try:
                reqdata = json.loads(reqbody)
            except json.JSONDecodeError as ex:
                raise http400(str(ex))

            try:
                cls = reqdata['_class']
            except KeyError:
                msg = 'The class value was not supplied. Check input.'
                raise ValueError(msg)

            classes = ['user']

            if cls not in classes:
                raise http404('Invalid class')

            cls  = reduce(getattr, cls.split('.'), sys.modules[__name__])

            try:
                meth = reqdata['_method']
            except KeyError:
                msg = 'The method value was not supplied. Check input.'
                raise ValueError(msg)
            if meth[0] == '_':
                raise http404('Invalid method')

            data = getattr(cls, meth)(reqdata)


        except Exception as ex:
            if isinstance(ex, httperror):
                statuscode = ex.statuscode
            else:
                statuscode = '500 Internal Server Error'

            data = {'_exception': repr(ex)}

        else:
            statuscode = '200 OK'

        finally:
            data = json.dumps(data)
            data = bytes(data, 'utf-8')

            resheads=[
                ('Content-Length', str(len(data))),
                ('Content-Type', 'application/json'),
                ('Access-Control-Allow-Origin', '*'),

            ]

            sres(statuscode, resheads)
            return iter([data])

app = application()
    


class httperror(Exception):
    def __init__(self, statuscode, msg):
        self.statuscode = statuscode
        self.message = msg

    def __repr__(self):
        return self.message

class http404(httperror):
    def __init__(self, msg):
        super().__init__('404 Not Found', msg)

class http400(httperror):
    def __init__(self, msg):
        super().__init__('400 Bad Request', msg)

class user:

    @staticmethod
    def getuser(data):
        id = data['id']
        if id == 1:
            return {'email': 'jessehogan0@gmail.com'}
        elif id == 2:
            return {'email': 'dhogan.d@gmail.com'}
        elif id == 3:
            from time import sleep
            sleep(10)

            return {'email': 'sleepy@gmail.com'}
        else:
            raise ValueError('Invalid user id: ' + str(id))


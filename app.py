import json
import sys
from functools import reduce
import pdb; B=pdb.set_trace

def app(env, sres):
    try:
        try:
            reqsize = int(env.get('CONTENT_LENGTH', 0))
        except(ValueError):
            reqsize = 0

        reqbody = env['wsgi.input'].read(reqsize).decode('utf-8')
        reqdata = json.loads(reqbody)


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
            ('Content-length', str(len(data))),
            ('Content-type', 'application/json')
        ]

        sres(statuscode, resheads)
        return iter([data])

class httperror(Exception):
    def __init__(self, statuscode, msg):
        self.statuscode = statuscode
        self.message = msg

    def __repr__(self):
        return self.message

class http404(httperror):
    def __init__(self, msg):
        super().__init__('404 Not Found', msg)

class user:

    @staticmethod
    def getuser(data):
        print('in self')
        print(data)


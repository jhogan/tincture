import json
import sys
from functools import reduce

def app(env, sres):
    try:
        reqsize = int(env.get('CONTENT_LENGTH', 0))
    except(ValueError):
        reqsize = 0

    reqbody = env['wsgi.input'].read(reqsize).decode('utf-8')
    reqdata = json.loads(reqbody)

    cls  = reduce(getattr, reqdata['_class'].split('.'), sys.modules[__name__])
    meth = reqdata['_method']

    data = getattr(cls, meth)(reqdata)

    data = json.dumps(data)
    data = bytes(data, 'utf-8')

    resheads=[
        ('Content-type', 'text/plain'),
        ('Content-length', str(len(data))),
    ]

    sres('200 OK', resheads)
    return iter([data])


class user:

    @staticmethod
    def getuser(data):
        print('in self')
        print(data)


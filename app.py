import json
import sys
from functools import reduce
import pdb; B=pdb.set_trace
from pprint import pprint
import traceback
import re
import os

class application:
    def __init__(self):

        try:
            epiphanypath = os.environ['epiphanypath']
        except KeyError:
            print('WARNING: No Epiphany path found in environment')
        else:
            sys.path.append(epiphanypath)
            from configfile import configfile

            try:
                epiphany_yaml = os.environ['epiphany.yaml']
            except KeyError:
                print('WARNING: No config file found in environment')
            else:
                cfg = configfile.getinstance()
                cfg.file = epiphany_yaml

        try:
            ctrlpath = os.environ['ctrlpath']
        except KeyError:
            print('WARNING: No controller path found in environment')
        else:
            sys.path.append(ctrlpath)

        try:
            epiphenomenonpath = os.environ['epiphenomenonpath']
        except KeyError:
            print('WARNING: No Epiphenomenon path found in environment')
        else:
            sys.path.append(epiphenomenonpath)

        self.clear()

    def clear(self):
        self._requestbody = None
        self._requestsize = None
        self._requestdata = None
        self._class = None
        self._method = None

    @property
    def environment(self):
        return self._env 

    def demandvalid(self):
        if len(self.requestbody) == 0:
            raise http400('No data in body of request message.')

        try:
            reqdata = self.requestdata
        except json.JSONDecodeError as ex:
            raise http400(str(ex))

        try:
            cls = reqdata['_class']
        except KeyError:
            msg = 'The class value was not supplied.'
            raise http404(msg)

        try:
            meth = self.method
        except KeyError:
            msg = 'The method value was not supplied.'
            raise ValueError(msg)

        if meth[0] == '_':
            raise http403('Invalid method.')

        try:
            import ctrl
        except ImportError as ex:
            raise ImportError('Error importing controller: ' + str(ex))
        
    @property
    def requestsize(self):
        if self._requestsize == None:
            try:
                self._requestsize = int(self.environment.get('CONTENT_LENGTH', 0))
            except(ValueError):
                self._requestsize = 0
        return self._requestsize
           
    @property
    def requestbody(self):
        if self._requestbody == None:
            reqsize = self.requestsize
            self._requestbody = self.environment['wsgi.input'].read(reqsize).decode('utf-8')
        return self._requestbody

    @property
    def requestdata(self):
        if self._requestdata == None:
            reqbody = self.requestbody
            self._requestdata = json.loads(reqbody)
        return self._requestdata

    @property
    def class_(self):
        if self._class == None:
            reqdata = self.requestdata
            cls = reqdata['_class'] 
            self._class = reduce(getattr, cls.split('.'), sys.modules['ctrl'])
        return self._class

    @property
    def method(self):
        if self._method == None:
            reqdata = self.requestdata
            self._method = reqdata['_method']
        return self._method

    def __call__(self, env, sres):
        try:
            self.clear()

            self._env = env

            self.demandvalid()

            reqdata = self.requestdata

            cls, meth = self.class_, self.method

            obj = cls(self)

            data = getattr(obj, meth)()

            data = [] if data == None else data

        except Exception as ex:
            if isinstance(ex, httperror):
                statuscode = ex.statuscode
            else:
                statuscode = '500 Internal Server Error'

            # Get the stack trace
            tb = traceback.format_exception(etype=None, value=None, tb=ex.__traceback__)

            # The top and bottom of the stack trace don't correspond to frames, so remove them
            tb.pop(); tb.pop(0)

            tb = [re.split('\n +', f.strip()) for f in tb]

            data = {'_exception': repr(ex), '_traceback': tb}

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

class httperror(Exception):
    def __init__(self, statuscode, msg):
        self.statuscode = statuscode
        self.message = msg

    def __repr__(self):
        return self.message

class http422(httperror):
    def __init__(self, msg):
        super().__init__('422 Unprocessable Entity', msg)


class http404(httperror):
    def __init__(self, msg):
        super().__init__('404 Not Found', msg)

class http403(httperror):
    def __init__(self, msg):
        super().__init__('403 Forbidden', msg)


class http401(httperror):
    def __init__(self, msg):
        super().__init__('401 Unauthorized', msg)

class http400(httperror):
    def __init__(self, msg):
        super().__init__('400 Bad Request', msg)

class controller:
    def __init__(self, app):
        self._app = app

    @property
    def application(self):
        return self._app

    @property
    def data(self):
        return self.application.requestdata

    @property
    def _arguments(self):
        return self.application.requestdata['args']

    def getargument(self, arg):
        args = self._arguments
        try:
            return args[arg]
        except KeyError:
            raise http422('Argument not supplied: ' + arg)

app = application()

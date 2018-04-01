from configfile import configfile
from functools import reduce
from pprint import pprint
import json
import os
import pdb; B=pdb.set_trace
import re
import sys
import traceback

class application:
    Logformat = '"{0} {1}.{2}({3})" {4} {5}'
    def __init__(self):
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
            cls = reqdata['__class']
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
            wsgiinput = self.environment['wsgi.input']
            if type(wsgiinput) == dict:
                self._requestbody = wsgiinput
            else:
                reqsize = self.requestsize
                self._requestbody = self.environment['wsgi.input'].read(reqsize).decode('utf-8')
        return self._requestbody

    @property
    def requestdata(self):
        if self._requestdata == None:
            reqbody = self.requestbody
            if type(reqbody) == dict:
                self._requestdata = reqbody
            else:
                self._requestdata = json.loads(reqbody)
        return self._requestdata

    @property
    def class_(self):
        if self._class == None:
            reqdata = self.requestdata
            cls = reqdata['__class'] 
            self._class = reduce(getattr, cls.split('.'), sys.modules['ctrl'])
        return self._class

    @property
    def method(self):
        if self._method == None:
            reqdata = self.requestdata
            self._method = reqdata['__method']
        return self._method

    def __call__(self, env, sres):
        statuscode = None
        log = None

        try:    log = configfile.getinstance().logs.default
        except: pass

        try:
            self.clear()

            self._env = env

            self.demandvalid()

            reqdata = self.requestdata

            cls, meth = self.class_, self.method

            obj = cls(self)

            data = getattr(obj, meth)()

            data = [] if data == None else data

            try:
                br = data['__brokenrules']
                if len(br):
                    statuscode = '422 Unprocessable Entity'
            except KeyError:
                # If action return no __brokenrules
                data['__brokenrules'] = ''

            data['__exception'] = None

        except Exception as ex:
            if log: log.exception('')

            if isinstance(ex, httperror):
                statuscode = ex.statuscode
            else:
                statuscode = '500 Internal Server Error'

            # Get the stack trace
            tb = traceback.format_exception(etype=None, value=None, tb=ex.__traceback__)

            # The top and bottom of the stack trace don't correspond to frames, so remove them
            tb.pop(); tb.pop(0)

            tb = [re.split('\n +', f.strip()) for f in tb]

            data = {'__exception': repr(ex), '__traceback': tb}

        else:
            if not statuscode:
                statuscode = '200 OK'

        finally:
            # Log
            try:
                d, env = self.requestdata, self.environment
                addr, cls, meth, = env['REMOTE_ADDR'], d['__class'], d['__method']
                args, st, ua = str(d['__args']), statuscode[:3], env['HTTP_USER_AGENT']
                log.info (application.Logformat.format(addr, cls, meth, '',   st, ua))
                log.debug(application.Logformat.format(addr, cls, meth, args, st, ua))
            except:
                pass

            # Return data
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
        return self.application.requestdata['__args']

    def getargument(self, arg):
        args = self._arguments
        try:
            return args[arg]
        except KeyError:
            return None

    @staticmethod
    def convertbrokenrules(ent):
        brs = []
        for br in ent.brokenrules:
            brs.append({
                'property':  br.property,
                'message':   br.message,
                'type':      br.type
            })
        return brs

app = application()

import socket


class Redis:
    '''
    >>> rd = Redis()('FLUSHALL')

    >>> u'OK' == rd(['HMSET', 's', 'x', 3, 'y', 4], ['HGETALL', 's']).next()
    True
    >>> u'OK' == next(rd)
    True
    >>> [u'x', u'3', u'y', u'4'] == rd('SET', 'x', 4)('GET', 'x')[-3]
    True
    >>> list(rd)
    []

    >>> rd('SET', 'x', 55).strlen('x')
    2

    >>> r, = rd('HGET', 's', 'x')
    >>> r == u'3'
    True
    >>> r1, r2 = rd('HGET', 's', 'x')('HGET', 's', 'y')
    >>> (r1, r2) == (u'3', u'4')
    True
    >>> cmds = []
    >>> cmds.append(['ZADD', 'z', 3, 'x', 4, 'y'])
    >>> cmds.append(['ZRANGE', 'z', 0, -1, 'WITHSCORES'])
    >>> cmds.append(['DEL', 'z'])
    >>> r1, r2 = list(rd(*cmds))[:2]
    >>> (r1, r2) == (2, [u'x', u'3', u'y', u'4'])
    True

    >>> [u'PONG'] == list(rd(['PING'] * 100).__del__()('PING'))
    True

    >>> u'OK' == rd.monitor()
    True

    >>> rd(*([['PING']] * 10))
    Redis(host="127.0.0.1", port=6379)
    >>> 10 == ['PING' in next(rd) for i in range(20)].count(True)
    True
    '''
    def __init__(
            self, host='127.0.0.1', port=6379, socket='', db=0, password=''):
        self._socket = socket
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.__socket = None
        self.reply = 0
        self.buffer = b''

    @property
    def socket(self):
        if not self.__socket:
            if self._socket:
                self.__socket = socket.socket(
                    socket.AF_UNIX, socket.SOCK_STREAM)
                self.__socket.connect(self._socket)
            else:
                self.__socket = socket.socket(
                    socket.AF_INET, socket.SOCK_STREAM)
                self.__socket.connect((self.host, self.port))
            self.reply = 0
            self.buffer = b''
            if self.password:
                r, = self("AUTH", self.password)
            if self.db:
                r, = self("SELECT", self.db)
        return self.__socket

    def tostring(self, s):
        try:
            return s.encode('utf8')
        except Exception:
            return s

    def __call__(self, *args):
        if not args:
            return self
        if not isinstance(args[0], (list, tuple)):
            args = [args]
        e = None
        for i in range(3):
            try:
                length = len(args)
                for i, arg in enumerate(args):
                    cmds = [
                        '$%s\r\n%s' % (len(a), a) for a in map(str, arg) if a]
                    cmds.insert(0, '*%s' % len(cmds))
                    cmds.append('')
                    (
                        self.socket.sendall if i == length - 1
                        else self.socket.send
                    )(self.tostring('\r\n'.join(cmds)))
                self.reply += len(args)
                break
            except Exception as _e:
                e = _e
                self.__del__()
        else:
            raise e
        return self

    def next(self):
        while b'\r\n' not in self.buffer:
            self.buffer += self.socket.recv(1024)
        if self.reply > 0:
            self.reply -= 1
        head = self.buffer[:1]
        body, self.buffer = self.buffer[1:].split(b'\r\n', 1)
        if head == b'+':
            return body.decode('utf8')
        elif head == b':':
            return int(body)
        elif head == b'$':
            if body == b'-1':
                return None
            body = int(body)
            while len(self.buffer) < body + 2:
                self.buffer += self.socket.recv(1024)
            body, self.buffer = self.buffer[:body], self.buffer[body+2:]
            return body.decode('utf8')
        elif head == b'*':
            body = int(body)
            self.reply += body
            return [self.next() for i in range(body)]
        elif head == b'-':
            raise Exception(body)
        raise Exception('Wrong header: %s' % head)

    def __len__(self):
        return self.reply

    def __iter__(self):
        for i in range(self.reply):
            yield self.next()

    def __del__(self):
        if self.__socket:
            self.__socket.close()
            self.__socket = None
        return self

    def __getitem__(self, key):
        return list(self)[key]

    def __getattr__(self, name):
        if name.startswith('_'):
            return self.__str__()
        if self.reply > 1024:
            self.__del__()
        return lambda *args: self.__call__(name.upper(), *args)[-1]

    def __str__(self):
        return '%s(%s)' % (
            Redis.__name__,
            ('socket="%s"' % self._socket) if self._socket
            else 'host="%s", port=%s' % (self.host, self.port))

    __repr__ = __str__
    __next__ = next

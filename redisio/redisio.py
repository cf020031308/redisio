import socket


class Redis:
    def __init__(self, host='127.0.0.1', port=6379, db=0, password=''):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.__socket = None
        self.reply = 0
        self.buffer = ''

    @property
    def socket(self):
        if not self.__socket:
            self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.__socket.connect((self.host, self.port))
            self.reply = 0
            self.buffer = ''
            if self.password:
                r, = self("AUTH", self.password)
            if self.db:
                r, = self("SELECT", self.db)
        return self.__socket

    def __call__(self, *args):
        if not args:
            return self
        if not isinstance(args[0], (list, tuple)):
            args = [args]
        msg = []
        for arg in args:
            cmds = ['$%s\r\n%s' % (len(a), a) for a in map(str, arg) if a]
            if cmds:
                cmds.insert(0, '*%s' % len(cmds))
                cmds.append('')
                msg.append('\r\n'.join(cmds))
        msg = ''.join(msg)
        try:
            self.socket.sendall(msg)
        except:
            self.__del__()
            self.socket.sendall(msg)
        self.reply += len(args)
        return self

    def next(self):
        while '\r\n' not in self.buffer:
            self.buffer += self.socket.recv(1024)
        if self.reply > 0:
            self.reply -= 1
        head = self.buffer[0]
        body, self.buffer = self.buffer[1:].split('\r\n', 1)
        if head == '+':
            return body
        elif head == ':':
            return int(body)
        elif head == '$':
            if body == '-1':
                return None
            body = int(body)
            while len(self.buffer) < body + 2:
                self.buffer += self.socket.recv(1024)
            body, self.buffer = self.buffer[:body], self.buffer[body+2:]
            return body
        elif head == '*':
            body = int(body)
            self.reply += body
            return [self.next() for i in range(body)]
        elif head == '-':
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

    def __getitem__(self, key):
        return list(self)[key]

    def __getattr__(self, name):
        return lambda *args: self.__call__(name.upper(), *args)[-1]

    def __str__(self):
        return '%s%s' % (Redis, (self.host, self.port))

    __repr__ = __str__
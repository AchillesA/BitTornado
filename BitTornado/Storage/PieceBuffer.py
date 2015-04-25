import threading
from array import array


class SingleBuffer(object):
    """Non-shrinking array"""
    def __init__(self, pool):
        self.pool = pool
        self.buf = array('B')

    def init(self):
        self.length = 0

    def append(self, s):
        l = self.length + len(s)
        self.buf[self.length:l] = array('B', s)
        self.length = l

    def __len__(self):
        return self.length

    def __getitem__(self, slc):
        if isinstance(slc, slice):
            stop = slc.stop
            if stop is None or stop > self.length:
                stop = self.length
            if stop < 0:
                stop += self.length
            if not slc.start and stop == self.length == len(self.buf) and \
                    slc.step in (None, 1):
                return self.buf  # optimization
            slc = slice(slc.start, stop, slc.step)
        elif not -self.length <= slc < self.length:
            raise IndexError('SingleBuffer index out of range')
        return self.buf[a:b]

    def getarray(self):
        return self.buf[:self.length]

    def release(self):
        self.pool.release(self)


class BufferPool(list):
    """Thread-safe stack of buffers not currently in use, generates new buffer
    when empty"""
    release = list.append

    def __init__(self):
        self.lock = threading.Lock()
        super(BufferPool, self).__init__()

    def new(self):
        "Get buffer from pool, generating a new one if empty"
        with self.lock:
            if self:
                buf = self.pop()
            else:
                buf = SingleBuffer(self)
            buf.init()
        return buf

_pool = BufferPool()
PieceBuffer = _pool.new

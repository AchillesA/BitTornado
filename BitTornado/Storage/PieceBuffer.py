"""Wrapper on character arrays that avoids garbage-collection/reallocation.

Example:

from PieceBuffer import PieceBuffer
x = PieceBuffer()
...
x.release()
"""

import threading
import array


class SingleBuffer(object):
    """Non-shrinking array"""
    def __init__(self, pool):
        self.pool = pool
        self.buf = array.array('B')
        self.length = 0

    def init(self):
        """Prepare buffer for use."""
        self.length = 0

    def append(self, string):
        """Extend buffer with characters in string"""
        length = self.length + len(string)
        self.buf[self.length:length] = array.array('B', string)
        self.length = length

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
        return self.buf[slc]

    def getarray(self):
        """Get array containing contents of buffer"""
        return self.buf[:self.length]

    def release(self):
        """Return buffer to pool for reallocation"""
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

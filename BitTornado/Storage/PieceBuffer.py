"""Wrapper on character arrays that avoids garbage-collection/reallocation.

Example:

from PieceBuffer import PieceBuffer
x = PieceBuffer()
...
x.release()
"""

import threading
import array


class Pool(list):
    """Thread-safe stack of objects not currently in use, generates new object
    when empty.

    Use as a decorator. Decorated classes must have init() method to
    prepare them for reuse."""
    def __init__(self, klass):
        super(Pool, self).__init__()

        self.lock = threading.Lock()
        klass.release = lambda s: self.append(s)
        self.klass = klass

    def __call__(self):
        "Get object from pool, generating a new one if empty"
        with self.lock:
            obj = self.pop() if self else self.klass()
        obj.init()
        return obj


@Pool
class PieceBuffer(object):
    """Non-shrinking array"""
    def __init__(self):
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

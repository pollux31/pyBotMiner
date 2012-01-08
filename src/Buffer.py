"""
The Buffer class manages incoming data packet with asynchronous reading.
Data are not flushed at each read but when the size of the buffer becomes to high

The Standard class pack and unpack data corresponding to a standard Struct class

The String class pack and unpack data containing Sting
"""

import zlib
from struct import calcsize, unpack_from, pack

from Debug import debug


class Buffer(object):
    """ Buffer managent for network interface """
    def __init__(self):
        self.maxSize = 5000     # buffer max size
        self.maximum = 0        # to track the size max the buffer has reach
        self.empty()
        self.ptrPush = -1
    
    def push(self):
        """ Store the pointer position for a rollback """
        self.ptrPush = self.ptrRead
        
    def pop(self, rollback):
        """ rollback or commit the push action """
        if rollback == True:
            self.ptrRead= self.ptrPush
        self.ptrPush = -1    
        
    def empty(self):
        """ empty the buffer """
        self.buf = ""
        self.ptrRead = 0        # pointer for reading
        self.len = 0
    
    def append(self, data):
        """ Add data to buffer """
        deb = ""
        for x in data:
            deb += "%02X " % ord(x)
        global debug
        debug.buffer("<== : [%s]" % deb)
        self.buf += data
        self.len += len(data)
        if self.len > self.maximum:
            self.maximum = self.len 
        if (len(self.buf) > self.maxSize) and (self.ptrPush < 0):
            # remove data already red
            self.buf = self.buf[self.ptrRead:]  
            self.ptrRead = 0
            self.len = len(self.buf)
            
    def peek(self, size=1):
        """ 
        Get data from the buffer without changing the prtRead
        Return DATA, or raise IOError exception
        """
        ptrFin = self.ptrRead + size
        if ptrFin > self.len:
            # No more data
            raise IOError
        return self.buf[self.ptrRead:ptrFin]
    
    def get(self, size=1):
        """ 
        Get data from the buffer and update prtRead
        Return DATA, or  raise IOError exception
        """
        if self.ptrRead + size > self.len:
            # No more data
            raise IOError
        self.ptrRead += size
        data = self.buf[self.ptrRead-size:self.ptrRead]
        if (self.ptrRead >= self.len) and (self.ptrPush < 0):
            # empty buffer
            self.empty()
        return data
    
    def seek(self, size=1):
        """ Drop data from the buffer """
        self.ptrRead += size
        if (self.ptrRead >= self.len) and (self.ptrPush < 0):
            # empty buffer
            self.empty()

             
# -----------------------------------------------------------------------------
class Standard(object):        
    """ Management of Standard format """
    def __init__(self, fmt):
        self.fmt = '>'+fmt
        self.len = calcsize(self.fmt)
        
    def pack(self, cmd, *data):
        return pack(self.fmt, cmd, *data)

    def unpack(self, buf):
        try:
            data = buf.get(self.len)
        except:
            raise IOError
        return unpack_from(self.fmt, data)
    
        
# -----------------------------------------------------------------------------
class String(object):
    """ Management of format containing a String """
    def __init__(self, fmt):
        self.fmt = fmt
        
    def pack(self, cmd, *data):
        res = pack('B', cmd)
        i=0
        for f in self.fmt[1:]:
            if f == 'S':
                res += pack('!h', len(data[i])) + data[i].encode('utf-16be')
            else:
                res += pack('!'+f, data[i])
            i += 1
        return res

    
    def unpack(self, buf):
        res = ()
        buf.push()
        try:
            for fmt in self.fmt:
                if fmt == 'S':
                    data = buf.get(2)
                    l = unpack_from('>h', data)[0]
                    if l > 0:
                        data = buf.get(2*l)
                        res += data.decode("utf-16be"),
                    else:
                        res += "",
                else:
                    l = calcsize(fmt)
                    data = buf.get(l)
                    res += unpack_from('>'+fmt, data)
        except IOError:
            buf.pop(True)
            raise IOError

        buf.pop(False)
        return res


# -----------------------------------------------------------------------------
class MetaEntity(object):
    def __init__(self, fmt):
        self.fmt = fmt
        
    def unpackMetaData(self, buf):
        metadata = {}
        try:
            x = Standard("B").unpack(buf)[0]
            while x != 127:
                index = x & 0x1F # Lower 5 bits
                ty    = x >> 5   # Upper 3 bits
                if ty == 0: val = Standard("b").unpack(buf)[0]
                elif ty == 1: val = Standard("h").unpack(buf)[0] 
                elif ty == 2: val = Standard("i").unpack(buf)[0] 
                elif ty == 3: val = Standard("f").unpack(buf)[0] 
                elif ty == 4: val = String("S").unpack(buf)[0]
                elif ty == 5:
                    val = {}
                    val["id"]     = Standard("h").unpack(buf)[0]
                    val["count"]  = Standard("b").unpack(buf)[0]
                    val["damage"] = Standard("h").unpack(buf)[0]
                elif ty == 6:
                    val = []
                    for i in range(3):
                        val.append(Standard("i").unpack(buf))[0]
                else:
                    global debug
                    debug.error("Unknown type ty=%d for x=ox%02X" % (ty, x))
                metadata[index] = (ty, val)
                x = Standard("B").unpack(buf)[0]
        except IOError:
            raise IOError
        return metadata,
        
    def unpack(self, buf):
        res = ()
        buf.push()
        try:
            for fmt in self.fmt:
                if fmt == 'E':
                    data = self.unpackMetaData(buf)
                    res += data
                else:
                    l = calcsize(fmt)
                    data = buf.get(l)
                    res += unpack_from('>'+fmt, data)
        except IOError:
            buf.pop(True)
            raise IOError

        buf.pop(False)
        return res

        
# -----------------------------------------------------------------------------
class BlockSlot(object):
    def __init__(self, fmt):
        self.fmt = fmt
        
    def packSlot(self, *data):
        res = pack('!h', data[0])
        if data[0] <> -1:
            res += pack("!hh", data[1:])
        return res

    def pack(self, cmd, *data):
        res = pack('B', cmd)
        i=0
        for f in self.fmt[1:]:
            if f == 'W':
                res += packSlot(data[i])
            else:
                res += pack('!'+f, data[i])
            i += 1
        return res

    def unpackSlot(self, buf):
        try:
            id = Standard("h").unpack(buf)[0]
            if id == -1:
                res = (-1,)
            else:
                res = (id, Standard("h").unpack(buf)[0], Standard("h").unpack(buf)[0])
        except IOError:
            raise IOError
        return res
        
    def unpack(self, buf):
        res = ()
        buf.push()
        try:
            for fmt in self.fmt:
                if fmt == 'W':
                    data = self.unpackSlot(buf)
                    res += data
                else:
                    l = calcsize(fmt)
                    data = buf.get(l)
                    res += unpack_from('>'+fmt, data)
        except IOError:
            buf.pop(True)
            raise IOError

        buf.pop(False)
        return res



# -----------------------------------------------------------------------------
class Window(object):
    def unpackSlot(self, buf):
        try:
            id = Standard("h").unpack(buf)[0]
            if id == -1:
                res = (-1,)
            else:
                res = (id, Standard("h").unpack(buf)[0], Standard("h").unpack(buf)[0])
        except IOError:
            raise IOError
        return res
        
    def unpack(self, buf):
        res = ()
        buf.push()
        try:
            res = Standard("Bb").unpack(buf)
            count = Standard("h").unpack(buf)[0]
            res += count,
            for i in range(count):
                res += self.unpackSlot(buf)
        except IOError:
            buf.pop(True)
            raise IOError

        buf.pop(False)
        return res



# -----------------------------------------------------------------------------
class MetaChunk(object):
    """ Read a Chunk packet """
    def unpack(self, buf):
        res = ()
        buf.push()
        try:
            #get fields
            res = Standard("Bihibbb").unpack(buf)
            # get the compressed data len
            data = buf.get(4)
            size = unpack_from('>i', data)
            res += size
            # get the buffer
            data = buf.get(size[0])
            res += zlib.decompress(data),

        except IOError, zlib.error:
            buf.pop(True)
            raise IOError

        buf.pop(False)
        return res


# -----------------------------------------------------------------------------
class BlockArray(object):
    """ Read a Block Array packet """
    def unpack(self, buf):
        res = ()
        buf.push()
        try:
            #get fields
            res = Standard("Bii").unpack(buf)
            # get the array size
            data = buf.get(2)
            size = unpack_from('>h', data)[0]
            res += size,
            # get first buffer
            fmt = '>'+'h'*size
            data = buf.get(2*size)
            res += unpack_from(fmt, data)
            # get second buffer
            fmt = '>'+'b'*size
            data = buf.get(size)
            res += unpack_from(fmt, data)
            # get third buffer
            data = buf.get(size)
        except IOError:
            buf.pop(True)
            raise IOError

        buf.pop(False)
        return res


# -----------------------------------------------------------------------------
class ByteArray(object):
    """ Read a Block Array packet """
    def unpack(self, buf):
        res = ()
        buf.push()
        try:
            #get fields
            res = Standard("BhhB").unpack(buf)
            # get the array size
            size = res[3]
            # get first buffer
            fmt = '>'+'b'*size
            data = buf.get(size)
            res += unpack_from(fmt, data)
        except IOError:
            buf.pop(True)
            raise IOError

        buf.pop(False)
        return res


# -----------------------------------------------------------------------------
class BlockExplosion(object):
    """ Read a Explosion packet """
    def unpack(self, buf):
        res = ()
        buf.push()
        try:
            #get fields
            res = Standard("Bdddf").unpack(buf)
            # get the array size
            data = buf.get(4)
            size = unpack_from('>i', data)[0]
            res += size,
            # get records
            rec = ()
            for i in range(size):
                data = buf.get(3)
                rec += unpack_from(">bbb", data)
            res += rec
        except IOError:
            buf.pop(True)
            raise IOError

        buf.pop(False)
        return res

        
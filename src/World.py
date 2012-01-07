import numpy as np

#class Vector(object):
#    def __init__(self, x, y, z):
#        self.vect = np.array([x, y, z])

class Chunk(object):
    """ class to manage a chunk """
    def __init__(self, x, y, z, sx, sy, sz, chunkData):
        self.pos = (x, y, z)
        self.size = (sx, sy, sz)
        d = np.fromstring(chunkData[:sx*sy*sz], dtype=np.uint8)
        self.blockData = d.reshape(sx, sz, sy).swapaxes(1, 2)

#    def __getitem__(self, key):
#        return self.blockData[tuple(key)]
#    
#    def __setitem__(self, key, value):
#        self.blockData[tuple(key)] = value
#        
#    def getBlocks(self, value):
#        """ return the list of indices [x,y, z] where block are present in the Chunk """
#        return np.transpose(np.nonzero(self.blockData==value))


class World(object):
    """ class to manage the world """
    def __init__(self):
        self.chunks = {}
        
    def addChunk(self, x, y, z, sx, sy, sz, chunkData):
        chunk = Chunk(x, y, z, sx, sy, sz, chunkData)
        self.chunks[(x,y,z)] = chunk 

    
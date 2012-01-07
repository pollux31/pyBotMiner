'''
Debug class
'''

import logging

LEVEL = logging.DEBUG
#LEVEL = logging.INFO

FILTER = True       # Filter the packet displayed
BUFFER = False      # display octets received
SEND   = True      # display sent packets
CHUNK  = True      # display the chunk information

class Debug(object):
    
    def __init__(self):
        #logging.basicConfig(filename='example.log',level=logging.DEBUG)
        logging.basicConfig(level=LEVEL)
        
        self.packets = {
        #     ID: (Display, name
            0x00: ( False,"Keep alive"),
            0x01: (True,"Login request"),
            0x02: (True,"Handshake"),
            0x03: (True,"Chat message"),
            0x04: ( False,"Time update"),
            0x05: ( False,"Entity Equipment"),
            0x06: (True,"Spawn position"),
            0x07: (True,"Use entity"),                             # C --> S
            0x08: (True,"Update health"),
            0x09: (True,"Respawn"),                                # C --> S
            0x0A: (True,"Player"),                                 # C --> S
            0x0B: (True,"Player position"),                        # C --> S
            0x0C: (True,"Player look"),                            # C --> S
            0x0D: (True,"Player position & look"),
            0x0E: (True,"Player digging"),
            0x0F: (True,"Player block placement"),
            0x10: (True,"Holding change"),
            0x11: (True,"Use bed"),
            0x12: (True,"Animation"),
            0x13: (True,"Entity action"),                          # C --> S
            0x14: (True,"Named entity spawn"),
            0x15: ( False,"Pickup spawn"),
            0x16: (True,"Collect item"),
            0x17: (True,"Add object/vehicle"),
            0x18: ( False,"Mob spawn"),
            0x19: (True,"Entity: painting"),
            0x1A: (True,"Experience Orb"),
            0x1B: (True,"Stance update"),
            0x1C: ( False,"Entity velocity"),
            0x1D: ( False,"Destroy entity"),
            0x1E: (True,"Entity"),
            0x1F: (True,"Entity relative move"),
            0x20: ( False,"Entity look"),
            0x21: ( False,"Entity look and relative move"),
            0x22: ( False,"Entity teleport"),
            0x26: (True,"Entity status"),
            0x27: (True,"Attach entity"),
            0x28: (True,"Entity metadata"),
            0x29: (True,"Entity Effect"),
            0x2A: (True,"Remove Entity Effect"),
            0x2B: (True,"Experience"),
            0x32: ( False,"Pre chunk"),
            0x33: ( False,"Map chunk"),
            0x34: ( False,"Multi-block change"),
            0x35: ( False,"Block change"),
            0x36: (True,"Block action"),
            0x3C: (True,"Explosion"),
            0x3D: (True,"Sound effect"),
            0x46: (True,"New/invalid state"),
            0x47: (True,"Thunderbolt"),
            0x64: (True,"Open window"),
            0x65: (True,"Close window"),
            0x66: (True,"Window click"),
            0x67: (True,"Set slot"),
            0x68: (True,"Window items"),
            0x69: (True,"Update window property"),
            0x6A: (True,"Transaction"),
            0x6B: (True,"Creative inventory action"),
            0x6C: (True,"Enchant Item"),
            0x82: (True,"Update sign"),
            0x83: (True,"item data"),
            0xC8: (True,"Increment statistic"),
            0xC9: ( False,"Player List Item"),
            0xFF: (True,"Disconnect"),
        }

        
    def send(self, cmd, *data):
        ''' To trace packet sent '''
        if SEND:
            logging.debug("==> [0x%02X : %s]" % (cmd, str(data)))

    
    def received(self, ident):
        ''' To trace the packets received '''
        if ident not in self.packets:
            logging.error("*** unknown Id packet 0x%02X" % ident)
        elif FILTER and self.packets[ident][0] == False:
            return
        logging.debug("<== 0x%02X (%s)" %(ident, self.packets[ident][1]))
        
    def chunk(self, msg):
        ''' To trace the Chunks received '''
        if CHUNK:
            logging.debug(msg)
        
    def debug(self, msg):
        logging.debug(msg)
    
    def info(self, msg):
        logging.info(msg)
    
    def error(self, msg):
        logging.error(msg)
        
    def buffer(self, msg):
        if BUFFER:
            logging.debug(msg)
        
debug = Debug()

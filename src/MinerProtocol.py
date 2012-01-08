'''
Management of the Protocol between the Bot and the server
'''
import re
from twisted.internet.protocol import Protocol
from Buffer import Buffer, Standard, String, BlockSlot, Window, MetaEntity, MetaChunk, BlockArray, BlockExplosion, ByteArray
from MinerBot import MinerBot
from World import World
from Debug import debug
from Constant import BOT_NAME_NEEDED

class MinerProtocol(Protocol):
    """ implementation of the Minecraft protocol """
    def __init__(self, name):
        global debug
        self.log = debug
        self.bot = MinerBot(name, self.send)
        self.buffer = Buffer()
        self.world = World()
        self.packets = {
        #     ID: (function, format
            0x00: (self.onKeepAlive, Standard("Bi")),           # Keep alive
            0x01: (self.onLoginRequest, String("BiSqibbBB")),   # Login request
            0x02: (self.onHandshake, String("BS")),             # Handshake
            0x03: (self.onChat, String("BS")),                  # Chat message
            0x04: (None, Standard("Bq")),                       # Time update 
            0x05: (None, Standard("Bihhh")),                    # Entity Equipment
            0x06: (self.onSpawnPosition, Standard("Biii")),     # Spawn position
            0x07: (None, Standard("Bii?")),                     # Use entity  (C --> S)
            0x08: (self.onUpdateHealth, Standard("Bhhf")),      # Update health
            0x09: (None, Standard("Bbbbhl")),                   # Respawn  (C --> S)
            0x0A: (None, Standard("B?")),                       # Player  (C --> S)
            0x0B: (None, Standard("Bdddd?")),                   # Player position  (C --> S)
            0x0C: (None, Standard("Bff?")),                     # Player look  (C --> S)
            0x0D: (self.onPLayerPosition, Standard("Bddddff?")), # Player position & look
            0x0E: (None, Standard("Bbibib")),                   #  Player digging  (C --> S)
            0x0F: (None, BlockSlot("BibibW")),                  # Player block placement  (C --> S)
            0x10: (None, Standard("Bh")),                       # Holding change  (C --> S)
            0x11: (None, Standard("Bibibi")),                   # Use bed
            0x12: (None, Standard("Bib")),                      # Animation
            0x13: (None, Standard("Bib")),                      # Entity action  (C --> S)
            0x14: (self.onNamedEntitySpawn, String("BiSiiibbh")), # Named entity spawn
            0x15: (None, Standard("Bihbhiiibbb")),              # Pickup spawn
            0x16: (None, Standard("Bii")),                      # Collect item
            0x17: (self.onAddObject, Standard("Bibiiiihhh")),   # Add object/vehicle
            0x18: (None, MetaEntity("BibiiibbE")),              # Mob spawn
            0x19: (None, String("BiSiiii")),                    # Entity: painting
            0x1A: (None, Standard("Biiiih")),                   # Experience Orb
            0x1B: (None, Standard("Bffff??")),                  # Stance update
            0x1C: (None, Standard("Bihhh")),                    # Entity velocity
            0x1D: (None, Standard("Bi")),                       # Destroy entity
            0x1E: (None, Standard("Bi")),                       # Entity
            0x1F: (self.onEntityRelativeMove, Standard("Bibbb")), # Entity relative move
            0x20: (None, Standard("Bibb")),                     # Entity look
            0x21: (None, Standard("Bibbbbb")),                  # Entity look and relative move
            0x22: (None, Standard("Biiiibb")),                  # Entity teleport
            0x26: (None, Standard("Bib")),                      # Entity status
            0x27: (None, Standard("Bii")),                      # Attach entity
            0x28: (None, MetaEntity("BiE")),                    # Entity metadata
            0x29: (None, Standard("Bibbh")),                    # Entity Effect
            0x2A: (None, Standard("Bib")),                      # Remove Entity Effect
            0x2B: (None, Standard("Bfhh")),                     # Experience
            0x32: (self.onPreChunk, Standard("Bii?")),          # Pre chunk
            0x33: (self.onChunk, MetaChunk()),                  # Map chunk
            0x34: (None, BlockArray()),                         # Multi-block change
            0x35: (None, Standard("Bibibb")),                   # Block change
            0x36: (None, Standard("Bihibb")),                   # Block action
            0x3C: (None, BlockExplosion()),                     # Explosion
            0x3D: (None, Standard("Biibii")),                   # Sound effect
            0x46: (None, Standard("Bbb")),                      # New/invalid state
            0x47: (None, Standard("Bi?iii")),                   # Thunderbolt
            0x64: (None, String("BbbSb")),                      # Open window
            0x65: (None, Standard("Bb")),                       # Close window
            0x66: (None, BlockSlot("Bbhbh?W")),                 # Window click
            0x67: (None, BlockSlot("BbhW")),                    # Set slot
            0x68: (self.onWindowItems, Window()),               # Window items
            0x69: (None, Standard("Bbhh")),                     # Update window property
            0x6A: (self.onTransaction, Standard("Bbh?")),       # Transaction
            0x6B: (None, BlockSlot("BhW")),                     # Creative inventory action 
            0x6C: (None, Standard("Bbb")),                      # Enchant Item
            0x82: (None, String("BihiSSSS")),                   # Update sign
            0x83: (None, ByteArray()),                          # item data
            0xC8: (None, Standard("Bib")),                      # Increment statistic
            0xC9: (self.onPlayerList, String("BS?h")),          # Player List Item
            0xFF: (self.onDisconnected, String("BS")),          # Disconnect
        }


    def connectionMade(self):
        """ called when a connection has been established """
        self.log.info("<%s> connected" % self.bot.getName())
#        self.writer = PacketWriter(self.transport)
        self.log.debug("ATTEMPTING TO HANDSHAKE")
        self.sendHandshake(self.bot.getName())

    def connectionLost(self, reason):
        self.log.error("connection lost %s" % reason)

    def dataReceived(self, data):
        """ new data are received """ 
        self.buffer.append(data)

        while True:
            # get the packet Type
            try:
                data = self.buffer.peek()[0]
                packetType = ord(data)
            except IOError:   # if empty buffer stop the loop
                break
            self.log.received(packetType)

            # get the packet information
            if packetType not in self.packets:
                self.log.error("Unknown packet 0x%02X" % packetType)
                self.transport.loseConnection()
                
            fct, fmt = self.packets[packetType]
            try:
                packet = fmt.unpack(self.buffer)
            except IOError:
                break

            # do action on packet received
            if fct!= None:
                fct(self.bot, packet) 
    
  
    def onDisconnected(self, bot, info):
        self.log.info("Disconnected by server. Reason=%s" % info[1])

    def onKeepAlive(self, bot, info):
        self.send(0x00, 0)
    
    def onUpdateHealth(self, bot, info):
        bot.setHealth(health=info[1], food=info[2], foodSaturation=info[3])
        
    def onLoginRequest(self, bot, info):
        bot.setUID(info[1])
        #bot.setMaxSeed(info[3])
        pass
    
    def onHandshake(self, bot, info):
        #bot.setConnectionHash(info[1])
        self.sendLoginRequest(22, self.bot.getName())
        self.bot.nameToUpper()

    
    def onSpawnPosition(self, bot, info):
        bot.setSpawnPosition(info)
    
    def onPLayerPosition(self, bot, info):
        cmd, x, stance, y, z, yaw, pitch, onGround = info
        bot.setPlayerPosition(x, y, z, stance, yaw, pitch, onGround)
        self.send(0x0D, x, y, stance, z, yaw, pitch, onGround)

    def onEntityRelativeMove(self, bot, info):
        bot.setEntityRelativeMove(info)
    
    def onWindowItems(self, bot, info):
        pass
#        if info[1] == 0:
#            # inventory window
#            bot.setInventory(info[2], info[3])
#        else:
#            logging.error("Unknown window number=%d" % info[1])

#    def onSetSlot(self, bot, info):
#        if info[1] == 0:
#            bot.setSlotItem(info[1], info[2], info[3], info[4], info[5])
#            logging.debug("SetSlot %d, slot %d" %(info[1], info[2]))
    
    def onNamedEntitySpawn(self, bot, info):
        bot.setPlayerSpawn(info)
        
    def onAddObject(self):
        pass
    
    def onPreChunk(self, bot, info):
        pass
    
    def onChunk(self, bot, info):
        cmd, x, y, z, sx, sy, sz, compSize, chunkData = info
        # correct the real size
        sx += 1
        sy += 1
        sz += 1
        self.log.chunk("Chunk (x,y,z)=(%d, %d, %d) (sx,sy,sz)=(%d, %d, %d), len=%d" % (x, y, z, sx, sy, sz, len(chunkData)))
        self.world.addChunk(x, y, z, sx, sy, sz, chunkData)
    
    def onTransaction(self, bot, info):
        pass 
    
    def send(self, cmd, *data):
        if cmd not in self.packets:
            self.log.error("Unknown packet to send 0x%02X" % cmd)
            self.transport.loseConnection()
        fct, pack = self.packets[cmd]
        res = pack.pack(cmd, *data)
        deb = ""
        for x in res:
            deb += "%02X " % ord(x)
        self.transport.write(res)
        self.log.send(cmd)
    
    def sendDisconnect(self, reason):
        self.send(0xFF, "Disconnection by client")
        self.transport.loseConnection()

    def sendHandshake(self, userName):
        self.send(0x02, userName)

    def sendLoginRequest(self, protocol_version, username):
        self.send(0x01, protocol_version, username, 0, 0, 0, 0, 0, 0)
   
    def onChat(self, bot, info):
        '''
        Chat received. Analyse it to detect a message from the player 
        '''
        info = info[1].upper()
        if ord(info[0]) == 0xA7: #skip color code
            info = info[2:]
        # if the message is from a player it starts with <PlayerName>
        result = re.match("<(.*)>(.*)", info)
        if result == None:
            name = ""
            msg = info
        else:
            name = result.group(1)
            msg = result.group(2)
            result = msg.split()
            if BOT_NAME_NEEDED: # Command starts with the targeted Bot name
                if result[0] == bot.getName():
                    bot.parseCommand(name, result[1:])
            else:
                if name <> bot.getName():  # do not compute self message
                    bot.parseCommand(name, result)
                
    def onPlayerList(self, bot, info):
        bot.updatePlayerList(info[1], info[2])

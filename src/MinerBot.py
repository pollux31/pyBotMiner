"""
The Bot class to manage the miner
"""
from twisted.internet import task
from numpy import array

from Debug import debug
from Action import LookAt, Jump

class MinerBot(object):
    def __init__(self, name, fctSend):
        # Bot information
        self.name = name
        self.fctSend = fctSend      # function to call to send a message to the server
        self.health = 0
        self.food = 0
        self.foodSaturation = 0.0
        self.spawn = None           # Vector for the spawning position
        self.pos = None             # Vector for the bot position
        self.stance = 0.0
        self.yaw = 0.0
        self.pitch = 0.0
        self.onGroud = False

        # players information
        self.entityPos = {}
        self.entityEid = {}
                
        # command management
        global debug
        self.log = debug
        self.botTask = None
        self.commands = {}       # list of commands to execute
        
    def sendMsg(self, cmd, *arg):
        self.log.send(cmd, *arg)
        self.fctSend(cmd, *arg)
    
    def nameToUpper(self):
        self.name = self.name.upper()    

    def getName(self):
        return self.name
        
    def setSpawnPosition(self, info):
        cmd, x, y, z = info
        self.spawn = array([x, y, z])
        
    def setPlayerPosition(self, x, y, z, stance, yaw, pitch, onGround):
        self.pos = array([x, y, z])
        self.stance = stance
        self.yaw = yaw
        self.pitch = pitch
        self.onGroud = onGround
        self.log.debug("Player Position at %s" % str(self.pos))
        
        # run the Bot Task
        self.start()
        
    def setPlayerSpawn(self, info):
        cmd, eid, name, x, y, z, rotation, pitch, currentItem = info
        self.entityPos[eid] = array([x/32.0, y/32.0, z/32.0])
        self.entityEid[name.upper()] = eid
        self.log.debug("Player %s spawn at %s" % (name, str(self.entityPos[eid])))

        
    def setHealth(self, health, food, foodSaturation):
        self.health = health
        self.food = food
        self.foodSaturation = foodSaturation

    def updatePlayerList(self, name, onLine):
        pass
#        name = name.upper()
#        if onLine:
#            if name not in self.playerPos:
#                self.playerPos[name] = (0, 0, 0)
#        else:
#            if name in self.playerPos:
#                del self.playerPos[name]

    def setEntityRelativeMove(self, info):
        cmd, eid, dx, dy, dz = info
        if eid in self.entityPos:
            self.entityPos[eid] += (dx/32.0, dy/32.0, dz/32.0)
            
            
# --------------------------------------------------------------------------------
#   Task to manage the Bot actions 
# --------------------------------------------------------------------------------
    def stop(self):
        ''' Stop the Bot task '''
        if self.botTask:
            self.botTask.stop()
            self.botTask = None
        
    def start(self):
        ''' Start the Bot task '''
        if self.botTask: 
            return
        self.botTask = task.LoopingCall(self.run)
        self.botTask.start(0.5)
        
    def run(self):
        if len(self.commands):
            for value in self.commands.values():
                action, param = value
                action.run(param)
                

#        if len(self.commandQueue) > 0:
#            try:
#                v = self.commandQueue[0].next()
#                if v == False: #Something broke
#                    self.commandQueue.pop(0)
#            except Exception as ex:
#                if isinstance(ex, StopIteration):
#                    self.commandQueue.pop(0)
#                else:
#                    logging.error("Exception in command %r:" % self.commandQueue[0])
#                    logging.exception(ex)
#                    self.commandQueue.pop(0)
#        else:
#        #if not self.movedThisTick:
#            self.lookAt(self.lookTarget or (self.players and (min(self.players.values(),
#                            key=lambda p: (p.pos-self.pos).mag()).pos + (0, PLAYER_HEIGHT, 0))) or Point(0, 70, 0))
#            
#            try:
#                #fall
#                if self.map[self.pos + (0, -1, 0)] in BLOCKS_WALKABLE or (self.pos.y % 1) > 0.1:
#                    logging.info("falling...")
#                    y=0
#                    for y in xrange(ifloor(self.pos.y), -1, -1):
#                        if self.map[self.pos.x, y, self.pos.z] not in BLOCKS_WALKABLE:
#                            break
#                    self.queueCommand(self.command_moveTowards(Point(self.pos.x, y+1, self.pos.z)))
#            except BlockNotLoadedError:
#                pass
#        if not self.movedThisTick:
#            pass
#            #self.protocol.sendPacked(PACKET_PLAYERONGROUND, 1)
    
    
    def addCommand(self, cmd, action, param):
        ''' add a command in the list of task to do '''
        self.removeCommand(cmd)     # remove the command if existing
        # add the command in the to do list
        self.commands[cmd] = (action, param)
        self.log.debug("Add command : %s - %s" % (cmd, str(param)))
        
        
    def removeCommand(self, cmd):
        ''' remove a command from the list of tasks '''
        if cmd in self.commands:
            self.commands.pop(cmd)
            self.log.debug("Remove command : %s" % cmd)

    def parseCommand(self, player, cmd):
        ''' parse the command sent by the player with the Chat '''
        #self.log.debug("Chat >>> [%s] cmd = %s" % (player, str(cmd)))
        #self.send(0x03, "ok %s, your cmd is %s" % (player, str(cmd)))
        
        actionName = cmd[0]
        param = None
        toStop = False
        if actionName == 'STOP':
            actionName = cmd[1]
            toStop = True
            
        if actionName == "L":
            param = player
            action = LookAt(self, param)
        elif actionName == "LOOKAT":
            param = (lambda x: player if x == 'ME' else x)(cmd[1])
            action = LookAt(self, param)
        elif actionName == "J" or actionName == "JUMP":
            actionName = "JUMP"
            action = Jump(self)
        elif actionName == "Q" or actionName == "QUIT":
            self.stop()
            self.sendMsg(0xFF, "Fin !!!")
            return
        else:
            msg = "I don't understand %s" % actionName
            self.sendMsg(0x03, msg)
            self.log.error(msg)
            return
        
        if toStop:
            self.removeCommand(actionName)
        else:
            self.addCommand(actionName, action, param)    
    

        
'''
Management of the Bot actions

Each action is implemented in a specific class
The action is launched by the scheduler by calling the "run" methode of the class
'''

import math
from numpy import array_equal
from Debug import debug

class LookAt(object):
    ''' The boot must look at a specific player '''
    def __init__(self, bot, player):
        self.bot = bot
        self.playerPos = None
        self.playerEid = 0
        self.dir=0.0
        if player in self.bot.entityEid:
            self.visible = True
            self.bot.sendMsg(0x03, "Ok")
            self.playerEid = self.bot.entityEid[player]
        else:
            self.visible = False
            self.bot.sendMsg(0x03, "Sorry %s, I don't see you" % self.player)

    def run(self, param):
        if self.visible and self.playerEid in self.bot.entityPos:
            # test if we need to update the bot
            if array_equal(self.playerPos, self.bot.entityPos[self.playerEid]):
                return
            self.playerPos = self.bot.entityPos[self.playerEid].copy()
            global debug
            
            # compute direction
            dx, dy, dz = self.playerPos - self.bot.pos
            direction = math.degrees(math.atan2(-dx, dz))
            debug.debug("Look at dx=%f,dz=%f Direction=%d" % (dx, dz, direction))
            self.bot.sendMsg(0x0C, direction, 0.0, True)      # player look message
            #self.bot.sendMsg(0x0C, self.dir, 0.0, True)
            #self.dir += 10.0


class Jump(object):
    def __init__(self, bot):
        self.bot = bot
        self.cpt=0
        self.x, self.y, self.z = self.bot.pos
        self.stance = self.bot.stance - self.y
    def run(self, param):
        if self.cpt < 3:
            self.cpt += 1
            self.y += 1.0
            self.bot.sendMsg(0x0B, self.x, self.y, self.y+self.stance, self.z, 0)
        else:
            self.bot.sendMsg(0x0A, 1)
            self.bot.removeCommand("JUMP")
        
        
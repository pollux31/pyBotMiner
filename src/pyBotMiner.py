"""
pyBotMiner Main module

pyBotMiner is a Bot that can accept command from the chat line and do actions 

"""

from sys import argv
from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory
from MinerProtocol import MinerProtocol
from Debug import debug

class MinerClientFactory(ClientFactory):
    def __init__(self, name):
        global debug
        self.name = name
        self.log = debug

    def startedConnecting(self, connector):
        global debug
        self.log.debug("startedConnecting")

    def buildProtocol(self, addr):
        self.log.debug("Connected, starting protocol")
        protocol = MinerProtocol(self.name)
        return protocol

    def clientConnectionLost(self, connector, reason):
        self.log.debug('Lost connection.  Reason: %s' % reason)
        reactor.stop()

    def clientConnectionFailed(self, connector, reason):
        self.log.error('Connection failed. Reason: %s' % reason)
        reactor.stop()



if __name__ == '__main__':

    server = '127.0.0.1'
    port = 25565
    if len(argv) >= 2:
        name = argv[1]
    else:
        name = "X"
    
    reactor.connectTCP(server,port,MinerClientFactory(name))
    reactor.run()

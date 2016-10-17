#! /usr/bin/env python

# from https://raw.githubusercontent.com/crossbario/autobahn-python/master/examples/twisted/websocket/broadcast/server.py
import os
import sys
import json

from twisted.internet import reactor
from twisted.python import log
from twisted.web.server import Site
from twisted.web.static import File

from autobahn.twisted.websocket import WebSocketServerFactory, \
    WebSocketServerProtocol
from autobahn.twisted.resource import WebSocketResource

class ClientHandler(object):
    """A set of handlers for a client's role: unknown, snake, or admin"""
    def __init__(self, client):
        self.client = client

    def msg_handle(self, msg):
        func = 'onMessage_%s' % msg["msg"]
        if hasattr(self, func):
            getattr(self, func)(msg)
            return True
        return False

class ClientHandlerUnknown(ClientHandler):
    def onMessage_register_snake(self, msg):
        self.client.handler_add(ClientHandlerSnake)
        self.client.snake.msg_handle(msg)
            
    def onMessage_register_admin(self, msg):
        self.client.handler_add(ClientHandlerAdmin)
    
class ClientHandlerSnake(ClientHandler):
    def __init__(self, client):
        super(ClientHandlerSnake, self).__init__(client)
        self.client.snake = self.client.factory.snake_add(self.client)
        
    def onMessage_move(self, msg):
        self.client.snake.msg_handle(msg)

class ClientHandlerAdmin(ClientHandler):
    def onMessage_config(self, msg):
        if "turn_delay" in msg:
            self.client.factory.turn_delay = float(msg["turn_delay"])
            
    def onMessage_start(self, msg):
        self.client.factory.turn_start()

    def onMessage_pause(self, msg):
        self.client.factory.turn_pause()

    def onMessage_quit(self, msg):
        self.client.factory.turn_quit()

class Snake(object):
    """a snake"""
    def __init__(self, client):
        self.client = client
        self.pos = ()
        self.ttl = 0
        self.state = None
        self.color = None
        self.taunt = ""
        self.direction = 'N'

    def msg_handle(self, msg)
        for attr in "color label icon taunt state direction".split():
            if attr in msg:
                setattr(snake, attr, msg[attr])


class SnakeServerProtocol(WebSocketServerProtocol):
    """A client WebSocket connection.  May be a snake, admin, or watcher"""
    def __init__(self, *args, **kwargs):
        super(SnakeServerProtocol, self).__init__(*args, **kwargs)
        self.handlers = {}
        self.handler_add(ClientHandlerUnknown)
        
    def onOpen(self):
        super(SnakeServerProtocol, self).onOpen()
        self.factory.watcher_add(self)

    def connectionLost(self, reason):
        super(SnakeServerProtocol, self).connectionLost(reason)
        self.factory.client_remove(self)

    def onMessage(self, payload, isBinary):
        try:
            if isBinary:
                raise ValueError("Binary message: %s")
            msg = json.loads(payload.decode('utf8'))
            handled = False
            for handler in self.handlers:
                if handler.msg_handle(msg):
                    handled = True
            if not handled:
                self.send_json({'error': 'unknown message: %s' % payload})
                           
        except Exception as e:
            self.send_json({'error': "Exception receiving message from %s: %s\n%s\n" % (self.peer, e, payload)})

    def handler_add(self, handler_class):
        if handler_class not in self.handlers:
            self.handlers[handler_class] = handler_class(self)

    def send_json(self, obj):
        self.sendMessage(json.dumps(obj, ensure_ascii=False).encode('utf8'))
        

class SnakeServerFactory(WebSocketServerFactory):
    """
    A Battlesnake server:

        accept connections from snakes
        accept connections from watchers
        wait for start
        while True:
           broadcast board
           accept snake moves
           delay turn time
           move snakes
           check for death
    """

    def __init__(self, url):
        WebSocketServerFactory.__init__(self, url)

        self.board = Board()
        self.snakes = set()
        self.clients = set()

        self.turn_delay = 1
        self.turn_count = 0
        self.turn_paused = True

    def watcher_add(self, client):
        self.watchers.add(client)

    def watcher_remove(self, client):
        self.watchers.remove(client)

    def client_remove(self, client):
        self.watcher_remove(client)
        self.snake_remove(client)

    def snake_add(self, client):
        if client not in self.snakes:
            snake = Snake(client)
            self.snakes[client] = snake
            client.snake = snake
        self.watcher_remove(client)

    def board_send(self):
        # send board and snake state to snakes
        for snake in self.snakes:
            snake.client.send_json({
                'type': 'snake',
                'board': self.board,
                'snake': snake,
                })
            
        # send board to watchers
        msg = {
            'type': 'arena',
            'board': self.board,
            'snakes': self.snakes,
            'messages': self.messages,
            }
        msg = json.dumps(msg, ensure_ascii=False).encode('utf8')
        msg = self.prepareMessage(msg)
        for c in self.watchers:
            c.sendPreparedMessage(msg)

    def board_update(self):
        for snake in self.snakes:
            pass

    def turn_start(self):
        self.turn_paused = False
        self.turn_tick()

    def turn_pause(self):
        self.turn_paused = True
        
    def turn_quit(self):
        self.reactor.quit()
        
    def turn_tick(self, update=True):
        self.turn_count += 1
        if turn_count > 1:
            self.board_update()
        self.board_send()
        if not self.turn_paused():
            self.reactor.callLater(self.turn_delay, self.turn_tick)
            

if __name__ == '__main__':

    log.startLogging(sys.stdout)

    root = File(os.path.join(__file__, "static"))

    factory = SnakeServerFactory(u"ws://127.0.0.1:9000")
    factory.protocol = SnakeServerProtocol
    resource = WebSocketResource(factory)
    root.putChild(b"ws", resource)
    
    site = Site(root)
    reactor.listenTCP(9000, site)

    reactor.run()

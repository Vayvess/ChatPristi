from shared.constants import TcpMsg

# REQUEST HANDLERS
def room_join(server, sess, msg):
    room_name = msg.get(TcpMsg.DATA)
    if room_name is None:
        return
    
    if not isinstance(room_name, str):
        return
    
    server.room_manager.join(server, sess, room_name)

def room_echo(server, sess, msg):
    text = msg.get(TcpMsg.DATA)
    if text is None:
        return
    
    if not isinstance(text, str):
        return
    
    server.room_manager.echo(server, sess, text)

def room_list(server, sess, msg):
    server.room_manager.list(server, sess)

def room_create(server, sess, msg):
    pass

class Dispatcher:
    def __init__(self, server):
        self.server = server
        self.handlers = {
            TcpMsg.ROOM_JOIN: room_join,
            TcpMsg.ROOM_ECHO: room_echo,
            TcpMsg.ROOM_LIST: room_list
        }
    
    def dispatch(self, sess, msg):
        msgtype = msg.get(TcpMsg.TYPE)
        if msgtype is None:
            return
        
        handler = self.handlers.get(msgtype)
        if handler:
            handler(self.server, sess, msg)
        else:
            print(msgtype)

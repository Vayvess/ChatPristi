import logging
from shared.constants import TcpMsg

# REQUEST HANDLERS
def room_join(server, sess, msg):
    room_name = msg.get(TcpMsg.DATA)
    logging.info(f"{sess.usern} requested to join a room")
    if room_name is None:
        logging.warning(f"{sess.usern} sent suspicious packet: {msg}")
        return
    
    if not isinstance(room_name, str):
        logging.warning(f"{sess.usern} sent suspicious packet: {msg}")
        return
    
    server.room_manager.join(server, sess, room_name)
    logging.info(f"{sess.usern} joined {room_name}")

def room_echo(server, sess, msg):
    text = msg.get(TcpMsg.DATA)
    if text is None:
        logging.warning(f"{sess.usern} sent suspicious packet: {msg}")
        return
    
    if not isinstance(text, str):
        logging.warning(f"{sess.usern} sent suspicious packet: {msg}")
        return
    
    server.room_manager.echo(server, sess, text)
    logging.info(f"{sess.usern} echo: {msg} in {sess.curr_room}")

def room_list(server, sess, msg):
    server.room_manager.list(server, sess)
    logging.info(f"{sess.usern} requested the list of room")

def room_create(server, sess, msg):
    rname = msg.get(TcpMsg.DATA)
    if isinstance(rname, str):
        server.room_manager.create(server, sess, rname)
        logging.info(f"{sess.usern} requested to create the room {rname}")
    else:
        logging.warning(f"{sess.usern} sent suspicious packet: {msg}")

class Dispatcher:
    def __init__(self, server):
        self.server = server
        self.handlers = {
            TcpMsg.ROOM_JOIN: room_join,
            TcpMsg.ROOM_ECHO: room_echo,
            TcpMsg.ROOM_LIST: room_list,
            TcpMsg.ROOM_CREATE: room_create
        }
    
    def dispatch(self, sess, msg):
        if not isinstance(msg, dict):
            logging.warning(f"{sess.usern} sent suspicious packet: {msg}")
            return
        
        msgtype = msg.get(TcpMsg.TYPE)
        if msgtype is None:
            logging.warning(f"{sess.usern} sent suspicious packet: {msg}")
            return
        
        handler = self.handlers.get(msgtype)
        if handler:
            handler(self.server, sess, msg)
        else:
            logging.warning(f"{sess.usern} sent suspicious packet: {msg}")

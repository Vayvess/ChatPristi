import json
from shared.constants import TcpMsg

def serialize_msg(msg):
    serialized = bytearray()
    encoded = json.dumps(msg).encode()
    header = len(encoded).to_bytes(2, 'big')
    serialized.extend(header)
    serialized.extend(encoded)
    return serialized

class Room:
    def __init__(self, name):
        self.name = name
        self.sessions = set()
    
    def broadcast_msg(self, server, msg):
        packet = serialize_msg(msg)
        for sess in self.sessions:
            server.send_packet(sess, packet)
    
    def add_sess(self, server, sess):
        self.sessions.add(sess)
        self.broadcast_msg(server, {
            TcpMsg.TYPE: TcpMsg.ROOM_JOINED,
            TcpMsg.DATA: (sess.usern, self.name)
        })
    
    def remove_sess(self, server, sess):
        self.sessions.discard(sess)
        self.broadcast_msg(server, {
            TcpMsg.TYPE: TcpMsg.ROOM_ECHO,
            TcpMsg.DATA: f"[bold purple]Server:[/bold purple] {sess.usern} left the room"
        })
    
    def echo(self, server, sess, text):
        echoed = f"{sess.usern}: {text}"
        packet = serialize_msg({
            TcpMsg.TYPE: TcpMsg.ROOM_ECHOED,
            TcpMsg.DATA: echoed
        })

        for sess in self.sessions:
            server.send_packet(sess, packet)

class RoomManager:
    def __init__(self):
        self.rooms = {
            'default': Room('default'),
            'alpha': Room('alpha'),
            'bravo': Room('bravo'),
            'charlie': Room('charlie'),
            'delta': Room('delta'),
            'echo': Room('echo'),
            'foxtrot': Room('foxtrot'),
            'golf': Room('golf'),
            'hotel': Room('hotel')
        }
    
    def join(self, server, sess, name):
        room = self.rooms.get(name)
        if room is None:
            return
        
        prev_room = self.rooms.get(sess.curr_room)
        if prev_room:
            prev_room.remove_sess(server, sess)
        
        sess.curr_room = name
        room.add_sess(server, sess)
    
    def echo(self, server, sess, text):
        room = self.rooms.get(sess.curr_room)
        if room is None:
            return
        
        room.echo(server, sess, text)
    
    def list(self, server, sess):
        room_list = tuple(k for k in self.rooms)
        packet = serialize_msg({
            TcpMsg.TYPE: TcpMsg.ROOM_LISTED,
            TcpMsg.DATA: room_list
        })

        server.send_packet(sess, packet)
    
    def leave(self, server, sess):
        room = self.rooms.get(sess.curr_room)
        if room is None:
            return
        


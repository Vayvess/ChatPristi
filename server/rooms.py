import json
import time

from shared.constants import TcpMsg

def serialize_msg(msg):
    serialized = bytearray()
    encoded = json.dumps(msg).encode()
    header = len(encoded).to_bytes(2, 'big')
    serialized.extend(header)
    serialized.extend(encoded)
    return serialized

class Room:
    def __init__(self):
        self.sessions = []
    
    def add_sess(self, server, sess):
        self.sessions.append(sess)

        packet = serialize_msg({
            TcpMsg.TYPE: TcpMsg.ROOM_JOINED,
            TcpMsg.DATA: sess.usern
        })

        for sess in self.sessions:
            server.send_packet(sess, packet)
    
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
            'default': Room()
        }
    
    def join(self, server, sess, name):
        room = self.rooms.get(name)
        if room is None:
            return
        
        room.add_sess(server, sess)
    
    def echo(self, server, sess, text):
        room = self.rooms.get(sess.curr_room)
        if room is None:
            return
        
        room.echo(server, sess, text)

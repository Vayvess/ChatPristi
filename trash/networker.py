import json
import queue
import socket
import threading
import selectors

from textual.message import Message

class ConnectionLost(Message):
    """Sent by Networker when connection is lost."""

class Networker(threading.Thread):
    def __init__(self, app):
        super().__init__(daemon=True)

        self.app = app
        self.alive = True
        self.rbuff = bytearray()

        self.nsent = 0
        self.sbuff = bytearray()

        self.incoming = queue.Queue()
        self.outgoing = queue.Queue()

        self.selector = selectors.DefaultSelector()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def connect(self, host, port):
        try:
            self.sock.connect((host, port))
        except Exception as err:
            print("connect: ", err)
            return False

        self.sock.setblocking(False)
        self.selector.register(self.sock, selectors.EVENT_READ, None)
        return True
    
    def extract_tcpmsg(self, data):
        messages = []
        self.rbuff.extend(data)
        view = memoryview(self.rbuff)

        k = 0
        n = len(view)
        PREFIX_LEN = 2
        while True:
            if n - k < PREFIX_LEN:
                # NO MORE TO EXTRACT
                break

            # READS THE PREFIX LENGTH OF THE FRAME
            chunk_len = int.from_bytes(view[k : k + PREFIX_LEN], 'big')
            frame_len = PREFIX_LEN + chunk_len

            if n - k < frame_len:
                # WAITING FOR MORE DATA
                break
            
            chunk = view[k + PREFIX_LEN : k + frame_len]

            try:
                msg = json.loads(chunk.tobytes().decode('utf-8'))
            except json.JSONDecodeError as e:
                self.alive = False
                return [-1]
            else:
                messages.append(msg)

            k += frame_len
        
        # DROP THE K FIRST BYTES EXTRACTED
        if k > 0:
            self.rbuff = bytearray(view[k:])
        
        return messages
        
    
    def handle_tcpread(self):
        if not self.alive:
            return
        
        try:
            data = self.sock.recv(4096)
        except BlockingIOError:
            return
        except OSError:
            self.alive = False
            return
        
        if not data:
            self.alive = False
            return
        
        for msg in self.extract_tcpmsg(data):
            if msg == -1:
                self.alive = False
                return
            else:
                self.incoming.put(msg)
    
    def handle_tcpwrite(self):
        if not self.alive:
            return
        
        to_send = memoryview(self.sbuff)[self.nsent:]

        try:
            sent = self.sock.send(to_send)
        except BlockingIOError:
            return
        except OSError:
            self.alive = False
            return
        else:
            self.nsent += sent
        
        to_send.release()
        if self.nsent == len(self.sbuff):
            self.nsent = 0
            self.sbuff.clear()
            self.selector.modify(self.sock, selectors.EVENT_READ)
    
    def send_tcpmsg(self, msg):
        self.outgoing.put(msg)
    
    def drain_incoming(self, n=8):
        while n > 0:
            if self.incoming.empty():
                return None
            
            n -= 1
            yield self.incoming.get_nowait()
        
        return None
    
    def drain_outgoing(self, n=8):
        was_empty = len(self.sbuff) == 0
        while n > 0 and not self.outgoing.empty():
            msg = self.outgoing.get_nowait()
            encoded = json.dumps(msg).encode()
            blen = len(encoded).to_bytes(2, 'big')

            self.sbuff.extend(blen)
            self.sbuff.extend(encoded)
            n -= 1
        
        if was_empty and len(self.sbuff) > 0:
            self.selector.modify(self.sock, selectors.EVENT_READ | selectors.EVENT_WRITE)
    
    def run(self):
        while self.alive:
            self.drain_outgoing()
            events = self.selector.select(0.05)
            for key, mask in events:
                if mask & selectors.EVENT_READ:
                    self.handle_tcpread()
                if mask & selectors.EVENT_WRITE:
                    self.handle_tcpwrite()
        

        self.selector.unregister(self.sock)
        self.sock.close()
        self.selector.close()
        self.app.post_message(ConnectionLost())

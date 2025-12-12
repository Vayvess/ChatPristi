import json
import queue
import socket
import threading
import selectors

from textual.message import Message

class ConnectionLost(Message):
    """Sent by Networker when connection is lost."""

class Networker(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        
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
            # CHECK IF ENOUGH BYTES
            if n - k < PREFIX_LEN:
                break

            # READS THE PREFIX LENGTH OF THE FRAME
            chunk_len = int.from_bytes(view[k : k + PREFIX_LEN], 'big')
            frame_len = PREFIX_LEN + chunk_len

            # CHECK IF ENOUGH BYTES
            if n - k < frame_len:
                break
            
            chunk = view[k + PREFIX_LEN : k + frame_len]
            msg = json.loads(chunk.tobytes().decode('utf-8'))

            k += frame_len
            messages.append(msg)
        
        # DROP THE K FIRST BYTES EXTRACTED
        if k > 0:
            self.rbuff = bytearray(view[k:])
        
        return messages
        
    
    def handle_tcpread(self):
        if not self.alive:
            return
        
        data = self.sock.recv(4096)
        if data:
            for msg in self.extract_tcpmsg(data):
                self.incoming.put(msg)
        else:
            self.alive = False
            raise ConnectionResetError("Connection lost")
    
    def handle_tcpwrite(self):
        if not self.alive:
            return
        
        to_send = memoryview(self.sbuff)[self.nsent:]

        try:
            sent = self.sock.send(to_send)
        except BlockingIOError:
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
            n -= 1
            if self.incoming.empty():
                return None
            yield self.incoming.get_nowait()
        return None
    
    def drain_outgoing(self, n=8):
        was_empty = len(self.sbuff) == 0
        while n > 0 and not self.outgoing.empty():
            n -= 1
            msg = self.outgoing.get_nowait()

            encoded = json.dumps(msg).encode()
            blen = len(encoded).to_bytes(2, 'big')
            self.sbuff.extend(blen)
            self.sbuff.extend(encoded)
        
        if was_empty and len(self.sbuff) > 0:
            self.selector.modify(self.sock, selectors.EVENT_READ | selectors.EVENT_WRITE)
    
    def handle_network(self, timeout=0.05):
        self.drain_outgoing()
        events = self.selector.select(timeout)
        for key, mask in events:
            if mask & selectors.EVENT_READ:
                self.handle_tcpread()
            if mask & selectors.EVENT_WRITE:
                self.handle_tcpwrite()
    
    def dispose(self):
        try:
            self.selector.unregister(self.sock)
            self.sock.close()
            self.selector.close()
        except Exception as e:
            print("Networker: ", e)
        finally:
            self.alive = False
            self.incoming.put(-1)
    
    def run(self):
        try:
            while self.alive:
                self.handle_network()
        except Exception as e:
            print("Networker: ", e)
        finally:
            self.dispose()

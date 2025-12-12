import socket
import selectors

from server.session import Session
from server.dispatcher import Dispatcher
from server.rooms import RoomManager


class Server:
    def __init__(self, host, port):
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_sock.bind((host, port))
        self.tcp_sock.setblocking(False)
        self.tcp_sock.listen()

        self.selector = selectors.DefaultSelector()
        self.selector.register(self.tcp_sock, selectors.EVENT_READ, None)

        self.dispatcher = Dispatcher(self)
        self.room_manager = RoomManager()
    
    def handle_accept(self):
        try:
            sock, addr = self.tcp_sock.accept()
        except socket.error as err:
            print("accept: ", err)
        else:
            sock.setblocking(False)
            sess = Session(sock)
            self.selector.register(sock, selectors.EVENT_READ, sess)
    
    def close_session(self, sess: Session):
        if sess.alive:
            sess.alive = False
            print(f"{sess.usern} disconnected from server !")
            self.selector.unregister(sess.sock)
            sess.sock.close()
    
    def send_packet(self, sess, packet):
        if not sess.alive:
            return
        
        if len(sess.sbuff) == 0:
            RW_EVENT = selectors.EVENT_READ | selectors.EVENT_WRITE
            self.selector.modify(sess.sock, RW_EVENT, sess)
        
        sess.sbuff.extend(packet)
    
    def process_data(self, sess, data):
        if not sess.alive:
            return
        
        for msg in sess.extract_tcpmsg(data):
            if msg != -1:
                self.dispatcher.dispatch(sess, msg)
            else:
                self.close_session(sess)
                return
    
    def handle_tcpread(self, sess: Session):
        try:
            data = sess.sock.recv(4096)
        except OSError as e:
            self.close_session(sess)
        
        if data:
            self.process_data(sess, data)
        else:
            self.close_session(sess)
    
    def handle_tcpwrite(self, sess: Session):
        if not sess.alive:
            return
        
        to_send = memoryview(sess.sbuff)[sess.nsent:]

        try:
            sent = sess.sock.send(sess.sbuff)
        except BlockingIOError:
            return
        except OSError:
            self.close_session(sess)
            return
        else:
            sess.nsent += sent
        
        to_send.release()
        if sess.nsent == len(sess.sbuff):
            sess.nsent = 0
            sess.sbuff.clear()
            self.selector.modify(sess.sock, selectors.EVENT_READ, sess)
    
    def handle_network(self, timeout=None):
        events = self.selector.select(timeout)
        for key, mask in events:
            sess = key.data
            if sess is None:
                self.handle_accept()
            else:
                if mask & selectors.EVENT_READ:
                    self.handle_tcpread(sess)
                if mask & selectors.EVENT_WRITE:
                    self.handle_tcpwrite(sess)
    
    def run(self):
        while True:
            self.handle_network()
    
    def shutdown(self):
        print("\nShutting down...")
        try:
            self.selector.unregister(self.tcp_sock)
        except Exception:
            pass
        self.tcp_sock.close()

        for key in list(self.selector.get_map().values()):
            sess = key.data
            if sess is not None:
                self.close_session(sess)
        
        try:
            self.selector.close()
        except Exception:
            pass
        print("Server shutdown")

if __name__ == '__main__':
    server = Server('localhost', 3000)
    try:
        server.run()
    except KeyboardInterrupt as e:
        server.shutdown()

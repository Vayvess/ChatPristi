import socket
import selectors

import logging
import argparse

from server.session import Session
from server.dispatcher import Dispatcher
from server.rooms import RoomManager


class Server:
    def __init__(self):
        self.running = True
        self.selector = selectors.DefaultSelector()
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.dispatcher = Dispatcher(self)
        self.room_manager = RoomManager()
    
    def configure(self, host, port):
        self.tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_sock.bind((host, port))
        self.tcp_sock.listen()

        self.tcp_sock.setblocking(False)
        self.selector.register(self.tcp_sock, selectors.EVENT_READ, None)
    
    def handle_accept(self):
        try:
            sock, addr = self.tcp_sock.accept()
        except socket.error as err:
            logging.error(f"handle_accept: {err}")
        else:
            sock.setblocking(False)
            sess = Session(sock)
            logging.info(f"{sess.usern} established connection !")
            self.selector.register(sock, selectors.EVENT_READ, sess)
    
    def close_session(self, sess: Session):
        if sess.alive:
            self.room_manager.leave(self, sess)
            self.selector.unregister(sess.sock)
            sess.sock.close()
            sess.alive = False
            logging.info(f"{sess.usern} disconnected from server !")
    
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
                logging.info(f"{sess.usern} sent packet: {data}")
                self.dispatcher.dispatch(sess, msg)
            else:
                logging.info(f"{sess.usern} sent corrupted message")
                self.close_session(sess)
                return
    
    def handle_tcpread(self, sess: Session):
        try:
            data = sess.sock.recv(4096)
        except OSError as e:
            logging.error(f"handle_tcpread: {sess.usern}, {e}")
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
        except OSError as e:
            logging.error(f"handle_tcpwrite: {sess.usern}, {e}")
            self.close_session(sess)
            return
        else:
            sess.nsent += sent
        
        to_send.release()
        if sess.nsent == len(sess.sbuff):
            sess.nsent = 0
            sess.sbuff.clear()
            self.selector.modify(sess.sock, selectors.EVENT_READ, sess)
    
    def run(self):
        while self.running:
            # HANDLE NETWORK
            events = self.selector.select()
            for key, mask in events:
                sess = key.data
                if sess is None:
                    self.handle_accept()
                else:
                    if mask & selectors.EVENT_READ:
                        self.handle_tcpread(sess)
                    if mask & selectors.EVENT_WRITE:
                        self.handle_tcpwrite(sess)
    
    def shutdown(self):
        try:
            self.selector.unregister(self.tcp_sock)
        except Exception as err:
            logging.error(f"Server shutdown: {err}")
        self.tcp_sock.close()

        for key in list(self.selector.get_map().values()):
            sess = key.data
            if sess is not None:
                self.close_session(sess)
        
        try:
            self.selector.close()
        except Exception as err:
            logging.error(f"Server shutdown: {err}")
        
        logging.info(f"Server shutdown")


def main():
    parser = argparse.ArgumentParser(description="IRC Server using TCP")

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Display debug logs"
    )

    parser.add_argument(
        "--addr",
        default="localhost",
        help="Bind address (default: localhost)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Port to listen on (default: 3000)"
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    server = Server()
    server.configure(args.addr, args.port)

    try:
        logging.info(f"\nServer is listening on {args.addr}:{args.port}")
        server.run()
    except KeyboardInterrupt:
        logging.info("\nShutting down server...")
        server.shutdown()

if __name__ == "__main__":
    main()
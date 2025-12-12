from textual.app import App

from client.networker import Networker
from client.screens.room import RoomScreen
from client.screens.connect import ConnectScreen
from client.screens.splash import SplashScreen


class Client(App):
    CSS_PATH = "./app.tcss"

    def on_mount(self):
        self.networker = None
        self.dispatcher = None
        self.push_screen(ConnectScreen())
    
    def _stop_networker(self):
        self.networker = None
        if self.dispatcher:
            self.dispatcher.stop()
            self.dispatcher = None
        

        while len(self.screen_stack) > 1:
            self.pop_screen()
        
        self.push_screen(ConnectScreen())
        self.notify("Server went offline", severity="error")
    
    def _dispatch_tcpmsg(self):
        for tcpmsg in self.networker.drain_incoming():
            if tcpmsg == -1:
                self._stop_networker()
                return
            else:
                self.screen.handle_tcpmsg(tcpmsg)
    
    def _boot_networker(self, addr, port):
        self.networker.start()
        self.dispatcher = self.set_interval(
            0.05, self._dispatch_tcpmsg
        )
        self.push_screen(RoomScreen())
    
    def try_connect(self, addr, port):
        self.notify("Connecting attempt...", severity="information")

        if self.networker is None:
            self.networker = Networker()
        
        ok = self.networker.connect(addr, port)

        if ok:
            self.notify(f"Connected to {addr} on port {port}",severity="success")
            self._boot_networker(addr, port)
        else:
            self.notify("Connection failed...", severity="error")
    
    def send_tcpmsg(self, msg):
        if self.networker:
            self.networker.send_tcpmsg(msg)
        else:
            self.notify("Not connected to a server", severity="warning")

if __name__ == '__main__':
    client = Client()
    client.run()

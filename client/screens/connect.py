from textual import (
    events, on
)

from textual.screen import Screen
from textual.containers import Vertical

from textual.widgets import (
    Input, Button, Label, 
    Footer, Header, Static,
)

class ConnectScreen(Screen):

    def compose(self):
        yield Header()
        with Vertical(id="connect_layout"):
            yield Label(
                content="Connect to [bold red]Server[/bold red]",
                id="connect_title"
            )
            yield Input(
                value="localhost",
                placeholder="address",
                id="connect_inputaddr"
            )
            yield Input(
                value="3000",
                placeholder="port",
                id="connect_inputport"
            )
            yield Button(
                label="Connect", 
                id="connect_btntryconnect"
            )
        yield Footer()
    
    @on(Button.Pressed, "#connect_btntryconnect")
    def connect(self, event):
        addr = self.query_one("#connect_inputaddr", Input).value.strip()
        port = self.query_one("#connect_inputport", Input).value.strip()

        try:
            port = int(port)
        except ValueError:
            self.app.notify(
                "Port must be a number.",
                severity="error"
            )
            return
        
        self.app.try_connect(addr, port)
    
    def handle_tcpmsg(self, tcpmsg):
        pass

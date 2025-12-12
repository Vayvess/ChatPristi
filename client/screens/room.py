from textual import on
from textual.screen import Screen
from textual.containers import (
    ScrollableContainer,
    Horizontal,
    Vertical,
)

from textual.widgets import (
    Input, Button, Label, 
    Footer, Header, Static,
)

from textual.widgets import (
    Input, Button, Label, 
    Footer, Header, Static,
)

from shared.constants import TcpMsg

class RoomScreen(Screen):

    def on_mount(self):
        self.messages = []
        self.app.send_tcpmsg({
            TcpMsg.TYPE: TcpMsg.ROOM_JOIN,
            TcpMsg.DATA: "default"
        })
    
    def compose(self):
        yield Header()
        with Vertical(id="room_layout"):
            with ScrollableContainer(id="room_logpanel"):
                yield Static(
                    content="",
                    id="room_logs"
                )
            with Horizontal(id="room_inputbar"):
                yield Input(
                    placeholder="Type your message...",
                    id="room_textinput"
                )
                yield Button(
                    label="Send",
                    id="room_btnsend"
                )
        yield Footer()
    
    def log_text(self, text):
        self.messages.append(text)
        logs_widget = self.query_one("#room_logs", Static)
        logs_widget.update("\n".join(self.messages))
        logpanel = self.query_one("#room_logpanel", ScrollableContainer)
        logpanel.scroll_end()
    
    @on(Button.Pressed, "#room_btnsend")
    @on(Input.Submitted, "#room_textinput")
    def send(self, event):
        input_widget = self.query_one("#room_textinput", Input)
        text = input_widget.value.strip()
        if text:
            input_widget.value = ""
            self.app.send_tcpmsg({
                TcpMsg.TYPE: TcpMsg.ROOM_ECHO,
                TcpMsg.DATA: text
            })
            
    
    def handle_roomjoined(self, msg):
        usern = msg.get(TcpMsg.DATA)
        self.log_text(f"[bold purple]Server:[/bold purple] {usern} joined the room")
    
    def handle_roomechoed(self, msg):
        text = msg.get(TcpMsg.DATA)
        self.log_text(text)
    
    def handle_tcpmsg(self, tcpmsg):
        mtype = tcpmsg.get(TcpMsg.TYPE)
        
        if mtype == TcpMsg.ROOM_JOINED:
            self.handle_roomjoined(tcpmsg)
        
        elif mtype == TcpMsg.ROOM_ECHOED:
            self.handle_roomechoed(tcpmsg)
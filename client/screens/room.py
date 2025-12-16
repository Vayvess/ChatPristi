from textual import on
from textual.screen import (
    Screen, ModalScreen
)

from textual.containers import (
    Container,
    ScrollableContainer,
    Horizontal, Vertical
)

from textual.widgets import (
    OptionList,
    Input, Button, Label, 
    Footer, Header, Static
)

from shared.constants import TcpMsg

class RoomListModal(ModalScreen):
    def __init__(self, rooms):
        super().__init__()
        self.rooms = rooms

    def compose(self):
        with ScrollableContainer():
            yield OptionList(
                *self.rooms,
                id="room_optionlist"
            )

    @on(OptionList.OptionSelected, "#room_optionlist")
    def on_select(self, event: OptionList.OptionSelected):
        self.dismiss(event.option.prompt)

class RoomCreateModal(ModalScreen):

    def compose(self):
        with Container():
            yield Input(
                placeholder="Type your room name...",
                id="inputroomname"
            )
            with Horizontal():
                yield Button.success("Confirm", id="confirm")
                yield Button.error("Back", id="back")
    
    @on(Button.Pressed, "#confirm")
    def on_confirm(self, event):
        input_widget = self.query_one("#inputroomname", Input)
        text = input_widget.value.strip()
        if text:
            self.dismiss(text)
        else:
            self.dismiss('')
    
    @on(Button.Pressed, "#back")
    def on_back(self, event):
        self.dismiss('')

class RoomScreen(Screen):

    def on_mount(self):
        self.logs = []
        self.room_name = 'default'

        self.app.send_tcpmsg({
            TcpMsg.TYPE: TcpMsg.ROOM_JOIN,
            TcpMsg.DATA: "default"
        })
    
    def compose(self):
        yield Header()
        with Vertical(id="room_layout"):
            with Horizontal(id="room_topbar"):
                yield Button(
                    label="Switch Room",
                    variant="default",
                    id="room_btnswitch"
                )
                
                yield Button(
                    label="Create Room",
                    variant="default",
                    id="room_btncreate"
                )

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
                    variant="primary",
                    id="room_btnsend"
                )
        yield Footer()
    
    def log_text(self, text):
        self.logs.append(text)
        logs_widget = self.query_one("#room_logs", Static)
        logs_widget.update("\n".join(self.logs))
        logpanel = self.query_one("#room_logpanel", ScrollableContainer)
        logpanel.scroll_end()
    
    @on(Button.Pressed, "#room_btnsend")
    @on(Input.Submitted, "#room_textinput")
    def room_echo(self, event):
        input_widget = self.query_one("#room_textinput", Input)
        text = input_widget.value.strip()
        if text:
            input_widget.value = ""
            self.app.send_tcpmsg({
                TcpMsg.TYPE: TcpMsg.ROOM_ECHO,
                TcpMsg.DATA: text
            })
    
    @on(Button.Pressed, "#room_btncreate")
    def room_create(self, event):
        def callback(room_name):
            if len(room_name) > 0:
                
                self.app.send_tcpmsg({
                    TcpMsg.TYPE: TcpMsg.ROOM_CREATE,
                    TcpMsg.DATA: room_name
                })
        
        self.app.push_screen(
            RoomCreateModal(),
            callback
        )
    
    @on(Button.Pressed, "#room_btnswitch")
    def select_room(self):
        self.app.send_tcpmsg({
            TcpMsg.TYPE: TcpMsg.ROOM_LIST
        })
    
    def handle_roomjoined(self, msg):
        usern, room_name = msg.get(TcpMsg.DATA)
        if self.room_name != room_name:
            self.logs = []
            self.room_name = room_name
        self.log_text(f"[bold purple]Server:[/bold purple] {usern} joined the [bold red]{room_name}[/bold red] channel")
    
    def handle_roomechoed(self, msg):
        text = msg.get(TcpMsg.DATA)
        self.log_text(text)
    
    def handle_roomlisted(self, msg):
        def on_roomselected(room):
            if room:
                self.app.send_tcpmsg({
                    TcpMsg.TYPE: TcpMsg.ROOM_JOIN,
                    TcpMsg.DATA: room
                })
        
        rooms = msg.get(TcpMsg.DATA, [])
        self.app.push_screen(
            RoomListModal(rooms),
            on_roomselected
        )
    
    def handle_tcpmsg(self, tcpmsg):
        mtype = tcpmsg.get(TcpMsg.TYPE)
        
        if mtype == TcpMsg.ROOM_JOINED:
            self.handle_roomjoined(tcpmsg)
        
        elif mtype == TcpMsg.ROOM_ECHOED:
            self.handle_roomechoed(tcpmsg)
        
        elif mtype == TcpMsg.ROOM_LISTED:
            self.handle_roomlisted(tcpmsg)

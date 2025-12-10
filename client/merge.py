import tkinter as tk

from shared.constants import *
from client.networker import Networker


class Client:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("My Tkinter App")
        self.root.geometry("800x600")

        # NETWORKING
        self.connected = False
        self.networker = None
        
        # Create the button
        self.button = tk.Button(self.root, text="connect", command=self.connect)
        self.button.pack(pady=20)

        self.button = tk.Button(self.root, text="test send", command=self.test_send)
        self.button.pack(pady=20)
    
    def connect(self):
        if self.connected:
            return
        
        self.networker = Networker()
        connected = self.networker.connect('localhost', 3000)
        if connected:
            self.connected = True
            self.networker.start()
        
        print(connected)
    
    def test_send(self):
        msg = {
            MsgField.TYPE : MsgType.LOGIN,
            MsgField.USERN: "Anto25",
            MsgField.PASSW: "admin123"
        }
        
        self.networker.send(msg)

    def on_close(self):
        self.root.destroy()
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()
        

if __name__ == "__main__":
    client = Client()
    client.run()

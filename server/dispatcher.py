from shared.constants import MsgType, MsgField

# REQUEST HANDLERS
def handle_login(server, sess, msg):
    sess.usern = msg.get(MsgField.PASSW)
    server.send_msg(sess, msg)
    print(msg)

class Dispatcher:
    def __init__(self, server):
        self.server = server
        self.handlers = {
            MsgType.LOGIN: handle_login
        }
    
    def dispatch(self, sess, msg):
        msgtype = msg.get(MsgField.TYPE)
        if msgtype is None:
            return
        
        handler = self.handlers.get(msgtype)
        if handler:
            handler(self.server, sess, msg)

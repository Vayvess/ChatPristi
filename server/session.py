import json

class Session:
    SESSID = 1

    def __init__(self, sock):
        self.sock = sock
        self.alive = True
        self.rbuff = bytearray()

        self.nsent = 0
        self.sbuff = bytearray()
        
        # SESSION DATA
        self.sessid = Session.SESSID
        self.usern = f'anon{Session.SESSID}'
        self.curr_room = ''
        Session.SESSID += 1
    
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
    
    def __hash__(self):
        return self.sessid

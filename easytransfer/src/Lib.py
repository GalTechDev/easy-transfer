import json
import socket
import os

class Base_type:
    MSG = "msg"
    FILE_TRANSFER = "file_transfer"
    TRANSFER_INFO = "transfer_info"

    ASK_AUTH = "ask_auth"
    GIVE_AUTH = "give_auth"

    class Transfer_info:
        FILE_TRANSFER_INFO = "file_transfer_info"
        PROGRESS = "progress"
        STATUT = "statut"

class Base:
    def data(self) -> dict:
        pass

    def encode(self, format= "utf-8") -> bytes:
        return json.dumps(self.data()).encode(format)
    
    def send_to(self, client):
        pass


class Message(Base):
    def __init__(self, content="") -> None:
        self.type = Base_type.MSG
        self.content = content

    def data(self):
        return {"type":self.type, "content":self.content}
    
    def send_to(self, client: socket.socket):
        client.send(self.encode())

    def __str__(self) -> str:
        return self.content
    
class File(Base):
    def __init__(self, file_path, block_size=4096) -> None:
        self.type = Base_type.FILE_TRANSFER
        self.file_path = file_path
        self.size = len(self)
        file_info = os.path.splitext(file_path)
        self.file_name = file_info[0]
        self.file_ext = file_info[1]
        self.block_size = block_size


    def getSize(file_path) -> int:
        with open(file_path) as f:
            f.seek(0,2) 
            size = f.tell()
        return size
    
    def get_blocks(self):
        try:
            #i = 0
            with open(self.file_path, "rb") as f:
                while True:
                    data = f.read(self.block_size)
                    if not data:
                        print("no data")
                        break
                    #print(i)
                    #i+=1
                    yield data
        except Exception as e:
            print(e)
    
    def __len__(self):
        return File.getSize(self.file_path)
    
    def data(self) -> dict:
        return {"type":self.type, "size":self.size, "file_name":self.file_name, "file_ext":self.file_ext}

    def send_to(self, client: socket.socket):
        client.send(self.encode())

        t = Transfer(self, client)
        Transfer.transfer.update({"id":t})
        t.start()

class Transfer:
    transfer = {}
    def __init__(self, file: File, client: socket.socket) -> None:
        self.file = file
        self.transfered_bytes = 0
        self.client = client

    def start(self):
        with open(self.file.file_path, "br") as f:
            f.seek(0,0) 
            for b in self.file.get_blocks():
                self.client.send(b)

class Transfer_info(Base):
    def __init__(self, info_type, data={}) -> None:
        self.type = Base_type.TRANSFER_INFO
        self.info_type = info_type
        self.c_data = data

    def data(self):
        return {"type":self.type, "info_type":self.info_type, "data":self.c_data}
    
    def send_to(self, client: socket.socket):
        client.send(self.encode())
import socket
import threading
from tkinter import filedialog
import json
from .Lib import *

#HOST = input("Entrer ip: ")
#PORT = int(input("Entrer port: "))
FORMAT = 'utf-8'

class Client:
    def __init__(self, host, port, nickname, buffer=1024, callback_on_msg=None, callback_on_progress=None) -> None:
        self.host = host
        self.port = port
        self.addr = (host, port)
        self.nickname = nickname
        self.buffer = buffer

        self.callback_on_progress = callback_on_progress
        self.callback_on_msg = callback_on_msg

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect(self.addr)

        receive_thread = threading.Thread(target=self.receive, args=[callback_on_msg,callback_on_progress])
        receive_thread.start()

    def receive(self, callback_on_msg=None, callback_on_progress=None):
        while True:
            try:
                data_b: bytes = self.client.recv(self.buffer)

                data = data_b.decode(FORMAT)
                data_json: dict = json.loads(data)
                type = data_json.get("type")
                if type == Base_type.FILE_TRANSFER:
                    self.transfer(self.client, data_json)

                elif type == Base_type.TRANSFER_INFO:
                    if data_json.get("info_type") == Base_type.ASK_AUTH:
                        self.client.send(Transfer_info(Base_type.GIVE_AUTH, {"nickname":self.nickname}).encode())
                    elif data_json.get("info_type") == Base_type.Transfer_info.PROGRESS:
                        if callback_on_progress==None:
                            print(data_json)
                        else:
                            callback_on_progress(data_json)
                            print(data_json)
                            
                elif type == Base_type.MSG:
                    if callback_on_msg==None:
                        print(data_json)
                    else:
                        callback_on_msg(data_json)
                        print(data_json)
            except json.decoder.JSONDecodeError as e:
                print(f"Error in JSON : {data_json}")
            except Exception as e:
                print("Une erreur s'est provoqué!")
                self.client.close()
                raise e
                break

    def write(self):
        #consol only
        while True:
            msg = input('')
            if msg == "!file":
                f_name = filedialog.askopenfilename()
                self.send_file(f_name)
            else:
                self.send_msg(msg)

    def send_msg(self, msg):
        message = f"{self.nickname}: {msg}"
        self.client.send(Message(message).encode(FORMAT))

    def send_file(self, file_path):
        file = File(file_path, self.buffer)
        file.send_to(self.client)

    def close(self):
        self.client.close()

    def transfer(self, client: socket.socket, data_json: dict):
        file_ext = data_json.get("file_ext")
        file_ext = file_ext if file_ext != "" else ".txt"
        path = filedialog.asksaveasfilename(filetypes=((file_ext, f"*{file_ext}"), ("Any", f"*")), defaultextension=file_ext)
        run = True
        size_receve = 0
        total_size = data_json.get("size")

        print(data_json)
        while run:
            file: bytes = client.recv(self.buffer)
            with open(path, "ba") as f:
                f.write(file)
            size_receve+=len(file)
            
            print(f"file receve {size_receve}/{total_size}")
            if size_receve >= total_size:
                run = False

            info = Transfer_info(Base_type.Transfer_info.PROGRESS, {"actual":size_receve, "total":total_size})
            self.callback_on_progress(info.data())
            client.send(info.encode())
        msg = Message("transfer complet")
        self.callback_on_msg(msg.data())
        client.send(msg.encode())
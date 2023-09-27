from .Lib import *
import socket
import threading
from tkinter import filedialog
import json

FORMAT = 'utf-8'

###COMMANDS (mettre un point d'exclamation devant)###
STOP_SERVER = 'STOP' # Arret du serveur
KICK_SERVER = 'KICK' # Expulser un joueur
LIST_SERVER = 'LIST' # avoir la liste des joueur connecter
MP_SERVER = 'MP' # envoyer un message privée a un joueur

class Server:
    def __init__(self, host, port, buffer=1024, callback_on_msg=None, callback_on_progress=None) -> None:
        self.host = host
        self.port = port
        self.addr = (host, port)
        self.buffer = buffer

        self.callback_on_progress = callback_on_progress
        self.callback_on_msg = callback_on_msg

        # Server Initialisation
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(self.addr)
        self.server.listen()
        msg = Message(f'[STARTING]: Server host {self.host} is listening on port {self.port}')
        self.callback_on_msg(msg.data())
        print(msg)

        # Clients Info
        self.clients = []
        self.nicknames = []

        r_thread = threading.Thread(target=self.receive)
        r_thread.start()

    def broadcast(self, message: bytes):
        msg = Message(json.loads(message.decode(FORMAT)).get("content"))
        self.callback_on_msg(msg.data())
        print(msg)
        for client in self.clients:
            client.send(message)

    def kick_all(self):
        for client in self.clients:
            client.close()

    def handle(self, client: socket.socket):
        while True:
            try:
                # Broadcasting message
                data_b: bytes = client.recv(self.buffer)
                
                data = data_b.decode(FORMAT)
                data_json: dict = json.loads(data)
                if data_json.get("type") == Base_type.FILE_TRANSFER:
                    self.transfer(client, data_json)
                    #thread = threading.Thread(target=transfer, args=(client, data_json))
                    #thread.start()
                elif data_json.get("type") == Base_type.MSG:
                    self.broadcast(data_b)
            except Exception as e:
                #Removing and closing Client
                index = self.clients.index(client)
                self.clients.remove(client)
                nickname = self.nicknames[index]
                self.broadcast(Message(f'{nickname} left!').encode())
                self.nicknames.remove(nickname)
                print(e)
                break

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

    def receive(self):
        while True:
            try:
                # Accept Connection
                client, addr = self.server.accept()
                msg = Message(f'[CLIENT]: Connected with {addr}')
                self.callback_on_msg(msg.data())
                print(msg)

                # Request and Store NickName
                client.send(Transfer_info(Base_type.ASK_AUTH).encode())
                data_b: bytes = client.recv(self.buffer)
                data = data_b.decode(FORMAT)
                data_json: dict = json.loads(data)
                nickname = data_json.get("data",{}).get("nickname")
                self.nicknames.append(nickname)
                self.clients.append(client)
                print(self.nicknames)

                #Print and broadcast NickNames
                msg = Message(f'[CLIENT]: Nickname is {nickname}')
                self.callback_on_msg(msg.data())
                print(msg)
                self.broadcast(Message(f'{nickname} joined!').encode(FORMAT))
                client.send(Message('Connected to the server!').encode())

                #Start handeling thread from client
                thread = threading.Thread(target=self.handle, args=(client,))
                thread.start()
            except Exception as e:
                msg = Message('[SERVER]: Server has been terminated...')
                self.callback_on_msg(msg.data())
                print(msg)
                break

    def send_msg(self, command: str):
        if command == "":
            return
        elif command == '!':
            msg = Message(f'[HELP]: {STOP_SERVER} | {LIST_SERVER} | {KICK_SERVER} <user> | {MP_SERVER} <user>')
            self.callback_on_msg(msg.data())
            print(msg)
        elif command[0] == '!':
            command = command[1::]
            command = command.split(' ')
            
            if command[0] == STOP_SERVER:
                self.broadcast(Message('[SERVER]: shut down...').encode(FORMAT))
                self.kick_all()
                self.server.close()
                return
            
            elif command[0] == LIST_SERVER:
                msg = Message(f'[LIST]: {self.nicknames}')
                self.callback_on_msg(msg.data())
                print(msg)
            
            elif command[0] == KICK_SERVER:
                nick = ''
                try:
                    nick = command[1]
                except IndexError:
                    msg = Message('[ERROR]: Uncomplete command')
                    self.callback_on_msg(msg.data())
                    print(msg)
                
                if len(command) > 2:
                    reason = str([command[i] + ' ' for i in range(2,len(command))])
                else:
                    reason = 'not precised'
                
                try:
                    index = self.nicknames.index(nick)
                    self.clients[index].send(Message(f"You will be banned in few seconds for reason : {' '.join(reason)}").encode())
                    self.clients[index].close()
                except ValueError:
                    msg = Message('[ERROR]: Client not found')
                    self.callback_on_msg(msg.data())
                    print(msg)

            elif command[0] == MP_SERVER:
                nick = ''
                try:
                    nick = command[1]
                except IndexError:
                    msg = Message('[ERROR]: Uncomplete command')
                    self.callback_on_msg(msg.data())
                    print(msg)

                try:
                    message = [command[i] + ' ' for i in range(2,len(command))]
                    
                    try:
                        index = self.nicknames.index(nick)
                        self.clients[index].send(Message(f"[ServerMP]: {' '.join(message)}").encode())
                    except ValueError:
                        msg = Message('[ERROR]: Client not found')
                        self.callback_on_msg(msg.data())
                        print(msg)
                    
                except IndexError:
                    msg = Message('[ERROR]: Please enter a message to send')
                    self.callback_on_msg(msg.data())
                    print(msg)

            else:
                msg = Message(f"[ERROR]: command was not reconized")
                self.callback_on_msg(msg.data())
                print(msg)
        else:
            self.broadcast(Message(f'[SERVER]: {command}').encode())

    def promt(self):
        while True:
            command = input()
            self.send_msg(command)

    def close(self):
        self.server.close()
        

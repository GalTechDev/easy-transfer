from .Lib import *
import socket
import threading
from tkinter import filedialog
import json
# Connection Data
#HOST = input("IP : ")
#PORT = int(input("PORT: "))
HOST = "localhost"
PORT = 2021
ADDR = (HOST, PORT)
FORMAT = 'utf-8'

###COMMANDS (mettre un point d'exclamation devant)###
STOP_SERVER = 'STOP' # Arret du serveur
KICK_SERVER = 'KICK' # Expulser un joueur
LIST_SERVER = 'LIST' # avoir la liste des joueur connecter
MP_SERVER = 'MP' # envoyer un message privée a un joueur

# Server Initialisation
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)
server.listen()
print(f'[STARTING]: Server host {HOST} is listening on port {PORT}')

# Clients Info
clients = []
nicknames = []

def broadcast(message):
    print(f'[BROADCAST]: {message.decode(FORMAT)}')
    for client in clients:
        client.send(message)

def kick_all():
    for client in clients:
        client.close()

def handle(client: socket):
    while True:
        try:
            # Broadcasting message
            data_b: bytes = client.recv(1024*4)
            
            data = data_b.decode(FORMAT)
            data_json: dict = json.loads(data)
            if data_json.get("type") == Base_type.FILE_TRANSFER:
                transfer(client, data_json)
                #thread = threading.Thread(target=transfer, args=(client, data_json))
                #thread.start()
            elif data_json.get("type") == Base_type.MSG:
                broadcast(data_b)
        except Exception as e:
            #Removing and closing Client
            index = clients.index(client)
            clients.remove(client)
            nickname = nicknames[index]
            broadcast(Message(f'{nickname} left!').encode())
            nicknames.remove(nickname)
            print(e)
            break

def transfer(client, data_json):
    file_ext = data_json.get("file_ext")
    file_ext = file_ext if file_ext != "" else ".txt"
    path = filedialog.asksaveasfilename(filetypes=((file_ext, f"*{file_ext}"), ("Any", f"*")), defaultextension=file_ext)
    run = True
    size_receve = 0
    total_size = data_json.get("size")
    print(data_json)
    while run:
        file: bytes = client.recv(1024*4)
        with open(path, "ba") as f:
            f.write(file)
        size_receve+=len(file)
        
        print(f"file receve {size_receve}/{total_size}")
        if size_receve >= total_size:
            run = False

        client.send(Transfer_info(Base_type.Transfer_info.PROGRESS, {"actual":size_receve, "total":total_size}).encode())
    
    client.send(Message("transfer complet").encode())

def receive():
    while True:
        try:
            # Accept Connection
            client, addr = server.accept()
            print(f'[CLIENT]: Connected with {addr}')

            # Request and Store NickName
            client.send(Transfer_info(Base_type.ASK_AUTH).encode())
            data_b: bytes = client.recv(1024*4)
            data = data_b.decode(FORMAT)
            data_json: dict = json.loads(data)
            nickname = data_json.get("data",{}).get("nickname")
            nicknames.append(nickname)
            clients.append(client)
            print(nicknames)

            #Print and broadcast NickNames
            print(f'[CLIENT]: Nickname is {nickname}')
            broadcast(Message(f'{nickname} joined!').encode(FORMAT))
            client.send(Message('Connected to the server!').encode())

            #Start handeling thread from client
            thread = threading.Thread(target=handle, args=(client,))
            thread.start()
        except:
            print('[SERVER]: Server has been terminated...')
            break

def promt():
    while True:
        command = input()
        if command == "":
            continue
        if command[0] == '!':
            command = command[1::]
            command = command.split(' ')
            
            if command[0] == STOP_SERVER:
                broadcast(Message('[SERVER]: shut down...').encode(FORMAT))
                kick_all()
                server.close()
                break
            
            elif command[0] == LIST_SERVER:
                print(f'[LIST]: {nicknames}')
            
            elif command[0] == KICK_SERVER:
                nick = ''
                try:
                    nick = command[1]
                except IndexError:
                    print('[ERROR]: Uncomplete command')
                
                if len(command) > 2:
                    reason = str([command[i] + ' ' for i in range(2,len(command))])
                else:
                    reason = 'not precised'
                
                try:
                    index = nicknames.index(nick)
                    clients[index].send(Message(f"You will be banned in few seconds for reason : {' '.join(reason)}").encode())
                    clients[index].close()
                except ValueError:
                    print('[ERROR]: Client not found')

            elif command[0] == MP_SERVER:
                nick = ''
                try:
                    nick = command[1]
                except IndexError:
                    print('[ERROR]: Uncomplete command')

                try:
                    message = [command[i] + ' ' for i in range(2,len(command))]
                    
                    try:
                        index = nicknames.index(nick)
                        clients[index].send(Message(f"[ServerMP]: {' '.join(message)}").encode())
                    except ValueError:
                        print('[ERROR]: Client not found')
                    
                except IndexError:
                    print('[ERROR]: Please enter a message to send')

            else:
                print(f"[ERROR]: command was not reconized")
        else:
            broadcast(Message(f'[SERVER]: {command}').encode())

##START##
r_thread = threading.Thread(target=receive)
promt_thread = threading.Thread(target=promt)

r_thread.start()
promt_thread.start()

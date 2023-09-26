from easytransfer.src.client import Client
from easytransfer.src.server import Server
import tkinter as tk
from tkinter import filedialog, ttk

def host_server():
    global client, nickname, chat_input, text_box
    HOST = host_entry.get()
    PORT = int(port_entry.get())

    # Créer un socket client
    client = Server(HOST, PORT, callback_on_msg=display_message, callback_on_progress=update_bar)

    # Désactiver les champs d'adresse et de port
    host_entry.config(state=tk.DISABLED)
    port_entry.config(state=tk.DISABLED)
    nickname_entry.config(state=tk.DISABLED)
    connect_button.config(state=tk.DISABLED)
    host_button.config(state=tk.DISABLED)

    chat_input.config(state=tk.NORMAL)
    send_button.config(state=tk.NORMAL)

# Fonction pour se connecter au serveur
def connect_to_server():
    global client, nickname, chat_input, text_box
    HOST = host_entry.get()
    PORT = int(port_entry.get())
    nickname = nickname_entry.get()

    # Créer un socket client
    client = Client(HOST, PORT, nickname, callback_on_msg=display_message, callback_on_progress=update_bar)

    # Désactiver les champs d'adresse et de port
    host_entry.config(state=tk.DISABLED)
    port_entry.config(state=tk.DISABLED)
    nickname_entry.config(state=tk.DISABLED)
    connect_button.config(state=tk.DISABLED)
    host_button.config(state=tk.DISABLED)

    chat_input.config(state=tk.NORMAL)
    send_button.config(state=tk.NORMAL)
    file_button.config(state=tk.NORMAL)

# Fonction pour envoyer un message
def send_message():
    message = chat_input.get()
    if message:
        chat_input.delete(0, tk.END)
        client.send_msg(message)

# Fonction pour envoyer un fichier
def send_file():
    f_name = filedialog.askopenfilename()
    client.send_file(f_name)

# Fonction pour afficher les messages reçus
def display_message(data_json: dict):
    message = data_json.get("content")
    text_box.insert(tk.END, message + "\n")
    text_box.see(tk.END)

def update_bar(data_json: dict):
    actual = data_json.get("data", {}).get("actual")
    total = data_json.get("data", {}).get("total")
    loading_bar["value"] = (actual / total) * 100
    root.update_idletasks()

# Fonction pour fermer proprement l'application
def on_closing():
    if client:
        client.close()
    root.destroy()

client = None

# Créer la fenêtre tkinter
root = tk.Tk()
root.title("Client Chat")

# Champs pour le nom d'utilisateur
nickname_label = tk.Label(root, text="Nom d'utilisateur:")
nickname_label.pack()
nickname_entry = tk.Entry(root)
nickname_entry.pack()

# Champs pour l'adresse IP du serveur
host_label = tk.Label(root, text="Adresse IP du serveur:")
host_label.pack()
host_entry = tk.Entry(root)
host_entry.pack()

# Champs pour le port du serveur
port_label = tk.Label(root, text="Port du serveur:")
port_label.pack()
port_entry = tk.Entry(root)
port_entry.pack()

# Bouton de connexion
connect_button = tk.Button(root, text="Se connecter au serveur", command=connect_to_server)
connect_button.pack()

host_button = tk.Button(root, text="Lancer le serveur", command=host_server)
host_button.pack()

# Zone de texte pour afficher les messages
text_box = tk.Text(root)
text_box.pack()

# Champs de saisie pour le chat
chat_input = tk.Entry(root)
chat_input.config(state=tk.DISABLED)
chat_input.pack()

# Bouton pour envoyer un message
send_button = tk.Button(root, text="Envoyer", command=send_message)
send_button.config(state=tk.DISABLED)
send_button.pack()

# Bouton pour envoyer un fichier
file_button = tk.Button(root, text="Envoyer un fichier", command=send_file)
file_button.config(state=tk.DISABLED)
file_button.pack()

loading_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
loading_bar.pack()

# Gérer la fermeture de la fenêtre
root.protocol("WM_DELETE_WINDOW", on_closing)

# Lancer la boucle principale de tkinter
root.mainloop()

from easytransfer.src.client import Client
from easytransfer.src.server import Server
import tkinter as tk
from tkinter import filedialog, ttk
import time

# Obtenez la taille de la mémoire physique minimale (en octets)
MIN_BUFFER_SIZE = 1024

# Obtenez la taille de la mémoire physique maximale (en octets)
MAX_BUFFER_SIZE = 1024**3

buffer_size = MIN_BUFFER_SIZE

def host_server():
    global client, nickname, chat_input, text_box
    HOST = host_entry.get()
    PORT = int(port_entry.get())

    # Créer un socket client
    buffer_size = buffer_slide.get()
    client = Server(HOST, PORT, buffer_size, callback_on_msg=display_message, callback_on_progress=update_bar)

    # Désactiver les champs d'adresse et de port
    host_entry.config(state=tk.DISABLED)
    port_entry.config(state=tk.DISABLED)
    nickname_entry.config(state=tk.DISABLED)
    connect_button.config(state=tk.DISABLED)
    host_button.config(state=tk.DISABLED)
    buffer_slide.config(state=tk.DISABLED)

    chat_input.config(state=tk.NORMAL)
    send_button.config(state=tk.NORMAL)

# Fonction pour se connecter au serveur
def connect_to_server():
    global client, nickname, chat_input, text_box
    HOST = host_entry.get()
    PORT = int(port_entry.get())
    nickname = nickname_entry.get()

    # Créer un socket client
    buffer_size = buffer_slide.get()
    client = Client(HOST, PORT, nickname, buffer_size, callback_on_msg=display_message, callback_on_progress=update_bar)

    # Désactiver les champs d'adresse et de port
    host_entry.config(state=tk.DISABLED)
    port_entry.config(state=tk.DISABLED)
    nickname_entry.config(state=tk.DISABLED)
    connect_button.config(state=tk.DISABLED)
    host_button.config(state=tk.DISABLED)
    buffer_slide.config(state=tk.DISABLED)

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
    progress = (actual / total) * 100

    loading_bar["value"] = progress

    # Calculer la vitesse de transfert en Ko/s
    now = time.time()
    if hasattr(update_bar, "last_update"):
        elapsed_time = now - update_bar.last_update
        if elapsed_time > 1:
            speed = (actual / buffer_slide.get()) / elapsed_time
        else:
            speed = 0
    else:
        speed = 0

    update_bar.last_update = now

    # Calculer le temps restant en secondes
    remaining_bytes = total - actual
    if speed > 0:
        remaining_time = remaining_bytes / (speed * buffer_slide.get())
    else:
        remaining_time = 0

    # Formater le temps restant en minutes et secondes
    minutes, seconds = divmod(int(remaining_time), 60)
    remaining_time_str = f"{minutes} min {seconds} sec" if minutes > 0 else f"{seconds} sec"

    loading_label["text"] = f"Transféré : {int(progress)}%, Vitesse : {speed:.2f} Ko/s, Temps restant : {remaining_time_str}"

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

buffer_label = tk.Label(root, text="Buffer:")
buffer_label.pack()
buffer_slide = tk.Scale(root, from_=MIN_BUFFER_SIZE, to=MAX_BUFFER_SIZE, orient=tk.HORIZONTAL)
buffer_slide.set(buffer_size)
buffer_slide.pack()

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

loading_label = tk.Label(root, text="No file transfer")
loading_label.pack()
loading_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
loading_bar.pack()

# Gérer la fermeture de la fenêtre
root.protocol("WM_DELETE_WINDOW", on_closing)

# Lancer la boucle principale de tkinter
root.mainloop()

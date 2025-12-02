import tkinter as tk
from tkinter import simpledialog, messagebox
import subprocess
import threading
import sys
import time
from config import PROTOCOL, MSG_TYPES
from protocol import create_client_socket, Message

# --- Variables Globales ---
server_process = None
server_thread = None
is_server_running = False

# --- Clase Cliente Chat GUI ---
class GuiChatClient:
    def __init__(self, master_frame, log_callback):
        self.client_socket = None
        self.username = None
        self.running = False
        self.log_callback = log_callback
        
        # UI Elements
        self.frame = tk.Frame(master_frame, bg="#2b2b2b")
        
        # Chat Display
        self.chat_area = tk.Text(self.frame, bg="white", fg="black", font=("Arial", 10), state=tk.DISABLED)
        self.scrollbar = tk.Scrollbar(self.frame, command=self.chat_area.yview)
        self.chat_area.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_area.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Input Area
        self.input_frame = tk.Frame(self.frame, bg="#2b2b2b")
        self.input_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        self.msg_entry = tk.Entry(self.input_frame, font=("Arial", 12))
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.msg_entry.bind("<Return>", lambda e: self.send_message())
        
        self.send_btn = tk.Button(self.input_frame, text="Enviar", command=self.send_message, bg="#1e90ff", fg="white")
        self.send_btn.pack(side=tk.RIGHT)
        
        self.connect_btn = tk.Button(self.frame, text="Conectar al Chat", command=self.connect, bg="#28a745", fg="white", font=("Arial", 12))
        self.connect_btn.place(relx=0.5, rely=0.5, anchor="center") # Centered initially

    def log(self, msg):
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, msg + "\n")
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)

    def connect(self):
        if not is_server_running:
            messagebox.showerror("Error", "El servidor no está iniciado.")
            return

        username = simpledialog.askstring("Login", "Ingrese su nombre de usuario:")
        if not username:
            return
            
        try:
            self.client_socket = create_client_socket(PROTOCOL)
            self.client_socket.connect()
            self.username = username
            
            # Register
            msg = Message(MSG_TYPES['REGISTER'], self.username)
            self.client_socket.send(msg)
            
            self.running = True
            self.connect_btn.place_forget() # Hide connect button
            
            # Start receiver thread
            threading.Thread(target=self.receive_messages, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo conectar: {e}")

    def receive_messages(self):
        while self.running:
            try:
                msg = self.client_socket.receive()
                if not msg:
                    break
                
                display_text = ""
                if msg.msg_type == MSG_TYPES['REGISTER_OK']:
                    display_text = f"[SISTEMA] {msg.content}"
                elif msg.msg_type == MSG_TYPES['BROADCAST']:
                    display_text = msg.format_display()
                elif msg.msg_type == MSG_TYPES['PRIVATE']:
                    display_text = f"[PRIVADO] {msg.sender}: {msg.content}"
                elif msg.msg_type == MSG_TYPES['SERVER_MSG']:
                    display_text = f"[SERVIDOR] {msg.content}"
                elif msg.msg_type == MSG_TYPES['ERROR']:
                    display_text = f"[ERROR] {msg.content}"
                
                if display_text:
                    ventana.after(0, self.log, display_text)
                    
            except Exception as e:
                ventana.after(0, self.log, f"[ERROR DE CONEXIÓN] {e}")
                break
        
        self.running = False
        ventana.after(0, self.reset_ui)

    def send_message(self):
        if not self.running: return
        
        content = self.msg_entry.get().strip()
        if not content: return
        
        try:
            if content.startswith("/msg "):
                parts = content[5:].split(" ", 1)
                if len(parts) == 2:
                    recipient, text = parts
                    msg = Message(MSG_TYPES['PRIVATE'], self.username, text, recipient)
                    self.client_socket.send(msg)
                    self.log(f"[YO -> {recipient}] {text}")
            else:
                msg = Message(MSG_TYPES['BROADCAST'], self.username, content)
                self.client_socket.send(msg)
                self.log(f"[YO] {content}")
            
            self.msg_entry.delete(0, tk.END)
        except Exception as e:
            self.log(f"[ERROR AL ENVIAR] {e}")

    def reset_ui(self):
        self.connect_btn.place(relx=0.5, rely=0.5, anchor="center")
        self.log("[DESCONECTADO]")

# --- Funciones Principales ---

def log_server(message):
    def _update():
        server_log_area.insert(tk.END, message + "\n")
        server_log_area.see(tk.END)
    ventana.after(0, _update)

def run_server_process():
    global server_process, is_server_running
    try:
        server_process = subprocess.Popen(
            [sys.executable, "-u", "server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd="."
        )
        is_server_running = True
        log_server(">>> Servidor INICIADO")
        
        for line in iter(server_process.stdout.readline, ''):
            if line: log_server(line.strip())
            
        is_server_running = False
        log_server(">>> Servidor DETENIDO")
        ventana.after(0, update_server_btn_state)
        
    except Exception as e:
        log_server(f"Error crítico: {e}")
        is_server_running = False

def toggle_server():
    global server_process, is_server_running
    
    if is_server_running:
        # Apagar
        if server_process:
            server_process.terminate()
            server_process = None
        is_server_running = False
        boton_server.config(text="Prender Servidor", bg="#1e90ff")
    else:
        # Prender
        threading.Thread(target=run_server_process, daemon=True).start()
        boton_server.config(text="Apagar Servidor", bg="#dc3545")

def update_server_btn_state():
    if is_server_running:
        boton_server.config(text="Apagar Servidor", bg="#dc3545")
    else:
        boton_server.config(text="Prender Servidor", bg="#1e90ff")

def show_server_logs():
    chat_client.frame.pack_forget()
    server_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

def show_chat():
    server_frame.pack_forget()
    chat_client.frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

# --- Interfaz Gráfica ---
ventana = tk.Tk()
ventana.title("Sistema de Chat Redes")
ventana.geometry("700x600")
ventana.configure(bg="#2b2b2b")

# Header
titulo = tk.Label(ventana, text="Proyecto Redes", font=("Arial", 20, "bold"), bg="#2b2b2b", fg="white")
titulo.pack(pady=15)

# Botones Superiores
frame_controles = tk.Frame(ventana, bg="#2b2b2b")
frame_controles.pack(pady=10)

boton_server = tk.Button(frame_controles, text="Prender Servidor", bg="#1e90ff", fg="white", font=("Arial", 12), width=15, command=toggle_server)
boton_server.grid(row=0, column=0, padx=10)

boton_chat = tk.Button(frame_controles, text="Chatear", bg="#1e90ff", fg="white", font=("Arial", 12), width=15, command=show_chat)
boton_chat.grid(row=0, column=1, padx=10)

boton_logs = tk.Button(frame_controles, text="Ver Logs", bg="#6c757d", fg="white", font=("Arial", 12), width=15, command=show_server_logs)
boton_logs.grid(row=0, column=2, padx=10)

# --- Vistas ---

# 1. Server Logs View
server_frame = tk.Frame(ventana, bg="#2b2b2b")
server_log_area = tk.Text(server_frame, bg="black", fg="#00ff00", font=("Consolas", 10))
server_scroll = tk.Scrollbar(server_frame, command=server_log_area.yview)
server_log_area.configure(yscrollcommand=server_scroll.set)

server_scroll.pack(side=tk.RIGHT, fill=tk.Y)
server_log_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# 2. Chat View (Instancia)
chat_client = GuiChatClient(ventana, None)

# Iniciar mostrando logs
show_server_logs()

ventana.mainloop()
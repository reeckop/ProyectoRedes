import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os
import signal

class GestorChat:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de Chat TCP/UDP")
        self.root.geometry("500x500")
        
        self.proceso_servidor = None
        self.protocolo = tk.StringVar(value="TCP")

        # --- Interfaz ---
        
        # 1. Título
        lbl_titulo = tk.Label(root, text="Configuración del Chat", font=("Arial", 12, "bold"))
        lbl_titulo.pack(pady=10)

        # 2. Switch de Protocolo (Radiobuttons)
        frame_proto = tk.LabelFrame(root, text="Protocolo", padx=10, pady=5)
        frame_proto.pack(pady=5)
        
        self.rb_tcp = tk.Radiobutton(frame_proto, text="TCP", variable=self.protocolo, value="TCP")
        self.rb_tcp.pack(side=tk.LEFT, padx=10)
        
        self.rb_udp = tk.Radiobutton(frame_proto, text="UDP", variable=self.protocolo, value="UDP")
        self.rb_udp.pack(side=tk.LEFT, padx=10)

        # 3. Botón Servidor (Toggle)
        self.btn_servidor = tk.Button(root, text="ENCENDER SERVIDOR", bg="green", fg="white", 
                                      width=20, command=self.toggle_servidor)
        self.btn_servidor.pack(pady=15)

        # 4. Botón Nuevo Cliente
        self.btn_cliente = tk.Button(root, text="Abrir Nuevo Cliente", width=20, 
                                     command=self.abrir_cliente, state=tk.DISABLED)
        self.btn_cliente.pack(pady=5)

    def toggle_servidor(self):
        if self.proceso_servidor is None:
            # --- ENCENDER ---
            proto = self.protocolo.get()
            print(f"Iniciando servidor en modo {proto}...")
            
            # Comando para abrir en nueva consola
            cmd = [sys.executable, 'servidor.py', proto]
            
            # DETALLE IMPORTANTE:
            # En Windows 'creationflags=subprocess.CREATE_NEW_CONSOLE' abre una ventana aparte.
            # En Linux, tendrías que usar algo como: subprocess.Popen(['xterm', '-e', 'python3 servidor.py UDP'])
            if os.name == 'nt': # Windows
                self.proceso_servidor = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
            else: # Linux / Mac (intento genérico)
                # Si esto falla en Linux, instala xterm o usa gnome-terminal
                self.proceso_servidor = subprocess.Popen(cmd)

            # Actualizar GUI
            self.btn_servidor.config(text="APAGAR SERVIDOR", bg="red")
            self.btn_cliente.config(state=tk.NORMAL) # Habilitar botón clientes
            self.rb_tcp.config(state=tk.DISABLED)    # Bloquear cambio de protocolo
            self.rb_udp.config(state=tk.DISABLED)
            
        else:
            # --- APAGAR ---
            # Matamos el proceso
            if os.name == 'nt':
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.proceso_servidor.pid)])
            else:
                os.kill(self.proceso_servidor.pid, signal.SIGTERM)
            
            self.proceso_servidor = None
            
            # Actualizar GUI
            self.btn_servidor.config(text="ENCENDER SERVIDOR", bg="green")
            self.btn_cliente.config(state=tk.DISABLED)
            self.rb_tcp.config(state=tk.NORMAL)
            self.rb_udp.config(state=tk.NORMAL)

    def abrir_cliente(self):
        proto = self.protocolo.get()
        cmd = [sys.executable, 'cliente.py', proto]
        
        if os.name == 'nt':
            subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            # Linux: ajustar según la terminal instalada (xterm, gnome-terminal, etc)
            subprocess.Popen(cmd) 

    def on_closing(self):
        """Asegura que se cierre el servidor si cerramos la ventana del menú"""
        if self.proceso_servidor:
            self.toggle_servidor()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = GestorChat(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
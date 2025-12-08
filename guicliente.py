import tkinter as tk
from tkinter import scrolledtext, messagebox
import socket
import threading
import json
import sys
from datetime import datetime
import comun

# --- PALETA DE COLORES (Dark Theme) ---
COLOR_FONDO = "#1E1E1E"
COLOR_CHAT_BG = "#111111"
COLOR_TEXTO = "#F0F0F0"
COLOR_PROPIO = "#007ACC"    # Azul para mis mensajes
COLOR_AJENO = "#333333"     # Gris para otros
COLOR_SISTEMA = "#238636"   # Verde para mensajes del server
COLOR_BTN = "#2D2D2D"
COLOR_BTN_HOVER = "#3E3E3E"
FONT_MAIN = ("Fira Code", 11)
FONT_BOLD = ("Fira Code", 11, "bold")

class BotonRedondo(tk.Canvas):
    def __init__(self, parent, width, height, radius, text, command=None, bg_color=COLOR_BTN, fg_color=COLOR_TEXTO):
        super().__init__(parent, width=width, height=height, bg=COLOR_FONDO, highlightthickness=0)
        self.command = command
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.hover_color = COLOR_BTN_HOVER
        self.text_str = text
        self.radius = radius
        self.state = "normal"
        self.rect = self._draw_rounded_rect(2, 2, width-2, height-2, radius, self.bg_color)
        self.text_id = self.create_text(width/2, height/2, text=text, fill=self.fg_color, font=FONT_BOLD)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)

    def _draw_rounded_rect(self, x1, y1, x2, y2, r, color):
        points = (x1+r, y1, x1+r, y1, x2-r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y1+r, x2, y2-r, x2, y2-r, x2, y2, x2-r, y2, x2-r, y2, x1+r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y2-r, x1, y1+r, x1, y1+r, x1, y1)
        return self.create_polygon(points, fill=color, smooth=True)

    def on_enter(self, event):
        if self.state == "normal": self.itemconfig(self.rect, fill=self.hover_color)
    def on_leave(self, event):
        if self.state == "normal": self.itemconfig(self.rect, fill=self.bg_color)
    def on_click(self, event):
        if self.state == "normal" and self.command: self.command()

class ClienteGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Cliente Chat - Ricardo Cervantes")
        self.root.geometry("450x650")
        self.root.configure(bg=COLOR_FONDO)
        
        self.sock = None
        self.es_tcp = True
        self.nombre = ""
        self.conectado = False
        
        # Iniciar en pantalla de LOGIN
        self.construir_login()

    def construir_login(self):
        self.frame_login = tk.Frame(self.root, bg=COLOR_FONDO)
        self.frame_login.pack(expand=True, fill="both", padx=40, pady=40)

        tk.Label(self.frame_login, text="INGRESAR AL CHAT", font=("Fira Code", 18, "bold"), 
                 bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(pady=(0, 30))

        # Nombre
        tk.Label(self.frame_login, text="Nombre de Usuario:", font=FONT_MAIN, bg=COLOR_FONDO, fg="#AAAAAA").pack(anchor="w")
        self.entry_nombre = tk.Entry(self.frame_login, font=FONT_MAIN, bg="#333333", fg="white", insertbackground="white")
        self.entry_nombre.pack(fill="x", pady=(5, 15))

        # IP
        tk.Label(self.frame_login, text="IP del Servidor:", font=FONT_MAIN, bg=COLOR_FONDO, fg="#AAAAAA").pack(anchor="w")
        self.entry_ip = tk.Entry(self.frame_login, font=FONT_MAIN, bg="#333333", fg="white", insertbackground="white")
        self.entry_ip.insert(0, "127.0.0.1") # Default localhost
        self.entry_ip.pack(fill="x", pady=(5, 15))
        
        # Ayuda IP
        tk.Label(self.frame_login, text="(Usa 127.0.0.1 si es la misma PC,\no la IP local 192.168.x.x si es otra)", 
                 font=("Fira Code", 8), bg=COLOR_FONDO, fg="#666666").pack(pady=(0, 15))

        # Protocolo
        tk.Label(self.frame_login, text="Protocolo:", font=FONT_MAIN, bg=COLOR_FONDO, fg="#AAAAAA").pack(anchor="w")
        self.var_proto = tk.StringVar(value="TCP")
        frame_radio = tk.Frame(self.frame_login, bg=COLOR_FONDO)
        frame_radio.pack(pady=5)
        
        tk.Radiobutton(frame_radio, text="TCP", variable=self.var_proto, value="TCP", 
                       bg=COLOR_FONDO, fg=COLOR_TEXTO, selectcolor="#000000", font=FONT_MAIN).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(frame_radio, text="UDP", variable=self.var_proto, value="UDP", 
                       bg=COLOR_FONDO, fg=COLOR_TEXTO, selectcolor="#000000", font=FONT_MAIN).pack(side=tk.LEFT, padx=10)

        # Botón Conectar
        btn = BotonRedondo(self.frame_login, 200, 50, 20, "CONECTAR", command=self.conectar, bg_color="#238636")
        btn.pack(pady=30)

    def construir_chat(self):
        self.frame_login.destroy() # Borrar login
        
        self.frame_chat = tk.Frame(self.root, bg=COLOR_FONDO)
        self.frame_chat.pack(expand=True, fill="both")
        
        # Header
        header = tk.Frame(self.frame_chat, bg="#111111", height=50)
        header.pack(fill="x")
        lbl_info = tk.Label(header, text=f"{self.nombre} @ {self.entry_ip.get()} ({self.var_proto.get()})", 
                            font=FONT_BOLD, bg="#111111", fg=COLOR_TEXTO)
        lbl_info.pack(pady=15)

        # Area Mensajes
        self.txt_chat = scrolledtext.ScrolledText(self.frame_chat, bg=COLOR_CHAT_BG, fg=COLOR_TEXTO, 
                                                  font=FONT_MAIN, bd=0, padx=10, pady=10)
        self.txt_chat.pack(expand=True, fill="both", padx=10, pady=10)
        self.txt_chat.config(state=tk.DISABLED)
        
        self.txt_chat.tag_config("propio", foreground=COLOR_PROPIO)
        self.txt_chat.tag_config("ajeno", foreground="#DDDDDD")
        self.txt_chat.tag_config("privado", foreground="#E06C75") # Rojo suave
        self.txt_chat.tag_config("sistema", foreground=COLOR_SISTEMA)

        # Area Input
        frame_input = tk.Frame(self.frame_chat, bg=COLOR_FONDO)
        frame_input.pack(fill="x", padx=10, pady=(0, 20))

        self.entry_msg = tk.Entry(frame_input, font=FONT_MAIN, bg="#333333", fg="white", insertbackground="white")
        self.entry_msg.pack(side=tk.LEFT, fill="x", expand=True, ipady=5)
        self.entry_msg.bind("<Return>", lambda e: self.enviar_mensaje())

        btn_enviar = BotonRedondo(frame_input, 80, 40, 15, "ENVIAR", command=self.enviar_mensaje, bg_color=COLOR_PROPIO)
        btn_enviar.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Foco
        self.entry_msg.focus()

    def agregar_mensaje(self, usuario, texto, tipo, hora):
        self.txt_chat.config(state=tk.NORMAL)
        
        tag = "ajeno"
        display_text = f"[{hora}] {usuario}: {texto}"

        if tipo == "ERROR":
            tag = "sistema"
            display_text = f"!!! {texto}"
        elif tipo == "PRIVADO":
            tag = "privado"
            display_text = f"[{hora}] (Privado) {usuario}: {texto}"
        elif usuario == self.nombre:
            tag = "propio"
        elif usuario == "SERVER":
            tag = "sistema"

        self.txt_chat.insert(tk.END, display_text + "\n", tag)
        self.txt_chat.see(tk.END)
        self.txt_chat.config(state=tk.DISABLED)

    def conectar(self):
        self.nombre = self.entry_nombre.get().strip()
        target_ip = self.entry_ip.get().strip()
        proto_str = self.var_proto.get()

        if not self.nombre:
            messagebox.showerror("Error", "El nombre no puede estar vacío")
            return

        self.es_tcp = (proto_str == "TCP")
        comun.PROTOCOLO = socket.SOCK_STREAM if self.es_tcp else socket.SOCK_DGRAM
        comun.HOST = target_ip # Sobreescribimos la IP destino
        
        try:
            self.sock = socket.socket(socket.AF_INET, comun.PROTOCOLO)
            if self.es_tcp:
                self.sock.settimeout(5) # Timeout solo para conectar
                self.sock.connect((target_ip, comun.PORT))
                self.sock.settimeout(None) # Quitar timeout
            
            # Mandar registro
            reg = comun.empaquetar_mensaje("REGISTRO", self.nombre, "Hola")
            if self.es_tcp:
                self.sock.send(reg)
            else:
                self.sock.sendto(reg, (target_ip, comun.PORT))

            # Si llegamos aqui, iniciar hilo de escucha y cambiar pantalla
            self.conectado = True
            threading.Thread(target=self.hilo_recibir, daemon=True).start()
            self.construir_chat()

        except Exception as e:
            messagebox.showerror("Error de Conexión", f"No se pudo conectar a {target_ip}.\n\nDetalle: {e}")

    def hilo_recibir(self):
        while self.conectado:
            try:
                if self.es_tcp:
                    datos = self.sock.recv(comun.BUFSIZE)
                else:
                    datos, _ = self.sock.recvfrom(comun.BUFSIZE)
                
                if not datos: break

                msg = comun.desempaquetar_mensaje(datos)
                if msg:
                    if msg['tipo'] == "ERROR" and ("llena" in msg['contenido'] or "uso" in msg['contenido']):
                        self.root.after(0, lambda m=msg: messagebox.showerror("Error", m['contenido']))
                        self.root.after(0, self.root.destroy)
                        break
                    
                    hora = msg['fecha'].split(' ')[1]
                    self.root.after(0, lambda u=msg['usuario'], c=msg['contenido'], t=msg['tipo'], h=hora: 
                                    self.agregar_mensaje(u, c, t, h))
            except:
                break
        
        # Desconexion
        if self.conectado:
            self.root.after(0, lambda: messagebox.showinfo("Desconectado", "Se perdió la conexión con el servidor"))
            self.root.after(0, self.root.destroy)

    def enviar_mensaje(self):
        texto = self.entry_msg.get().strip()
        if not texto: return
        
        self.entry_msg.delete(0, tk.END)
        
        # Comandos
        if texto == "/salir":
            self.root.destroy()
            return
        
        tipo = "PUBLICO"
        destino = None
        contenido = texto

        # Detectar privado /p usuario mensaje
        if texto.startswith("/p "):
            partes = texto.split(" ", 2)
            if len(partes) >= 3:
                tipo = "PRIVADO"
                destino = partes[1]
                contenido = partes[2]
            else:
                self.agregar_mensaje("SISTEMA", "Uso incorrecto. Usa: /p [usuario] [mensaje]", "ERROR", "00:00")
                return

        paquete = comun.empaquetar_mensaje(tipo, self.nombre, contenido, destino)
        
        try:
            if self.es_tcp:
                self.sock.send(paquete)
            else:
                self.sock.sendto(paquete, (comun.HOST, comun.PORT))
        except:
            self.agregar_mensaje("SISTEMA", "Error enviando mensaje", "ERROR", "00:00")

    def on_closing(self):
        self.conectado = False
        if self.sock: self.sock.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ClienteGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
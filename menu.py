import tkinter as tk
from tkinter import scrolledtext
import subprocess
import sys
import os
import signal
import threading
import queue

# --- PALETA DE COLORES (MODERNA) ---
COLOR_FONDO = "#1E1E1E"       # Negro oscuro
COLOR_TEXTO = "#FFFFFF"       # Blanco puro
COLOR_SUBTITULO = "#AAAAAA"   # Gris (Igual que "Protocolo")
COLOR_CONSOLA = "#111111"     # Fondo de la consola
COLOR_BTN_OFF = "#2D2D2D"     # Botón inactivo
COLOR_BTN_HOVER = "#3E3E3E"   # Hover
COLOR_ACCENT_TCP = "#007ACC"  # Azul VS Code
COLOR_BTN_ON = "#238636"      # Verde
COLOR_BTN_ALERT = "#DA3633"   # Rojo

# --- FUENTES ---
FONT_TITULO = ("Fira Code", 20, "bold")
FONT_SUBTITULO = ("Fira Code", 10)  # Letra más chica para el autor
FONT_TEXTO = ("Fira Code", 11)
FONT_BOTON = ("Fira Code", 11, "bold")
FONT_CONSOLA = ("Fira Code", 9)

class BotonRedondo(tk.Canvas):
    def __init__(self, parent, width, height, radius, text, command=None, bg_color=COLOR_BTN_OFF, fg_color=COLOR_TEXTO):
        super().__init__(parent, width=width, height=height, bg=COLOR_FONDO, highlightthickness=0)
        self.command = command
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.hover_color = COLOR_BTN_HOVER
        self.text_str = text
        self.radius = radius
        self.state = "normal"

        self.rect = self._draw_rounded_rect(2, 2, width-2, height-2, radius, self.bg_color)
        self.text_id = self.create_text(width/2, height/2, text=text, fill=self.fg_color, font=FONT_BOTON)

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

    def set_color(self, color):
        self.bg_color = color
        self.itemconfig(self.rect, fill=color)
    
    def set_text(self, text):
        self.itemconfig(self.text_id, text=text)

    def set_disabled(self, disabled=True):
        if disabled:
            self.state = "disabled"
            self.itemconfig(self.rect, fill="#151515")
            self.itemconfig(self.text_id, fill="#555555")
        else:
            self.state = "normal"
            self.itemconfig(self.rect, fill=self.bg_color)
            self.itemconfig(self.text_id, fill=self.fg_color)


class GestorChat:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat TCP/UDP - Gestor de Servidor")
        self.root.geometry("720x480")
        self.root.configure(bg=COLOR_FONDO)
        
        self.proceso_servidor = None
        self.hilo_lectura = None
        self.protocolo = "TCP"
        self.cola_logs = queue.Queue()

        # --- CONTENEDOR PRINCIPAL ---
        frame_main = tk.Frame(root, bg=COLOR_FONDO)
        frame_main.pack(fill="both", expand=True, padx=20, pady=10)

        # 1. TÍTULO Y AUTOR
        # Título Grande
        tk.Label(frame_main, text="Chat TCP/UDP", font=FONT_TITULO,
                 bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(pady=(0, 2))
        
        # Subtítulo (Autor) - Color gris oscuro y letra chica
        tk.Label(frame_main, text="Por: Ricardo Cervantes", font=FONT_SUBTITULO,
                 bg=COLOR_FONDO, fg=COLOR_SUBTITULO).pack(pady=(0, 15))

        # 2. SELECTOR DE PROTOCOLO
        frame_proto = tk.Frame(frame_main, bg=COLOR_FONDO)
        frame_proto.pack(pady=(0, 10))

        tk.Label(frame_proto, text="Protocolo:", font=FONT_TEXTO, 
                 bg=COLOR_FONDO, fg=COLOR_SUBTITULO).pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_tcp = BotonRedondo(frame_proto, 80, 35, 15, "TCP", command=lambda: self.set_protocolo("TCP"))
        self.btn_tcp.pack(side=tk.LEFT, padx=5)
        
        self.btn_udp = BotonRedondo(frame_proto, 80, 35, 15, "UDP", command=lambda: self.set_protocolo("UDP"))
        self.btn_udp.pack(side=tk.LEFT, padx=5)

        self.set_protocolo("TCP")

        # 3. BOTÓN SERVIDOR
        self.btn_servidor = BotonRedondo(frame_main, 200, 40, 20, "ENCENDER SERVIDOR", 
                                         bg_color=COLOR_BTN_ON, command=self.toggle_servidor)
        self.btn_servidor.pack(pady=5)

        # 4. CONSOLA
        tk.Label(frame_main, text="> LOGS DEL SISTEMA:", font=("Fira Code", 8, "bold"),
                 bg=COLOR_FONDO, fg="#666666", anchor="w").pack(fill="x", pady=(10, 0))

        self.txt_consola = scrolledtext.ScrolledText(
            frame_main, bg=COLOR_CONSOLA, fg="#00FF00",
            font=FONT_CONSOLA, bd=0, highlightthickness=0
        )
        self.txt_consola.pack(fill="both", expand=True)
        self.txt_consola.config(state=tk.DISABLED)

        self.revisar_cola_logs()

    def set_protocolo(self, proto):
        if self.proceso_servidor: return
        self.protocolo = proto
        if proto == "TCP":
            self.btn_tcp.set_color(COLOR_ACCENT_TCP); self.btn_tcp.fg_color = "#FFFFFF"
            self.btn_udp.set_color(COLOR_BTN_OFF);    self.btn_udp.fg_color = "#AAAAAA"
        else:
            self.btn_udp.set_color(COLOR_ACCENT_TCP); self.btn_udp.fg_color = "#FFFFFF"
            self.btn_tcp.set_color(COLOR_BTN_OFF);    self.btn_tcp.fg_color = "#AAAAAA"
        
        self.btn_tcp.set_text("TCP"); self.btn_udp.set_text("UDP")

    def log(self, mensaje):
        self.txt_consola.config(state=tk.NORMAL)
        self.txt_consola.insert(tk.END, mensaje + "\n")
        self.txt_consola.see(tk.END)
        self.txt_consola.config(state=tk.DISABLED)

    def revisar_cola_logs(self):
        while not self.cola_logs.empty():
            self.log(self.cola_logs.get_nowait())
        self.root.after(100, self.revisar_cola_logs)

    def leer_output_servidor(self, proceso):
        try:
            for linea in iter(proceso.stdout.readline, ''):
                if linea: self.cola_logs.put(linea.strip())
                else: break
        except: pass

    def toggle_servidor(self):
        if self.proceso_servidor is None:
            # ENCENDER
            self.log(f"--- INICIANDO SERVIDOR ({self.protocolo}) ---")
            cmd = [sys.executable, '-u', 'servidor.py', self.protocolo]
            
            flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            self.proceso_servidor = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, creationflags=flags)

            self.hilo_lectura = threading.Thread(target=self.leer_output_servidor, args=(self.proceso_servidor,), daemon=True)
            self.hilo_lectura.start()

            self.btn_servidor.set_text("APAGAR SERVIDOR")
            self.btn_servidor.set_color(COLOR_BTN_ALERT)
            self.btn_tcp.set_disabled(True)
            self.btn_udp.set_disabled(True)
        else:
            # APAGAR
            self.log("--- APAGANDO SERVIDOR ---")
            if self.proceso_servidor:
                if os.name == 'nt': subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.proceso_servidor.pid)])
                else: os.kill(self.proceso_servidor.pid, signal.SIGTERM)
            self.proceso_servidor = None
            
            self.btn_servidor.set_text("ENCENDER SERVIDOR")
            self.btn_servidor.set_color(COLOR_BTN_ON)
            self.btn_tcp.set_disabled(False)
            self.btn_udp.set_disabled(False)
            self.set_protocolo(self.protocolo)

    def on_closing(self):
        if self.proceso_servidor: self.toggle_servidor()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = GestorChat(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
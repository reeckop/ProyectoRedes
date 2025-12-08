import tkinter as tk
from tkinter import scrolledtext
import subprocess
import sys
import os
import signal
import threading
import queue
import time

from guiservidor import COLOR_SISTEMA

# Paleta de colores
COLOR_FONDO = "#1E1E1E"
COLOR_TEXTO = "#FFFFFF"
COLOR_SUBTITULO = "#AAAAAA"
COLOR_CONSOLA = "#111111"
COLOR_BTN_OFF = "#2D2D2D"
COLOR_BTN_HOVER = "#3E3E3E"
COLOR_ACCENT_TCP = "#007ACC"
COLOR_BTN_ON = "#238636"
COLOR_BTN_ALERT = "#DA3633"

# Fuentes
FONT_TITULO = ("Segoe UI", 20, "bold")
FONT_SUBTITULO = ("Segoe UI", 10)
FONT_TEXTO = ("Segoe UI", 11)
FONT_BOTON = ("Segoe UI", 11, "bold")
FONT_CONSOLA = ("Consolas", 9)

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
        if self.state == "normal": 
            self.itemconfig(self.rect, fill=self.hover_color)

    def on_leave(self, event):
        if self.state == "normal": 
            self.itemconfig(self.rect, fill=self.bg_color)

    def on_click(self, event):
        if self.state == "normal" and self.command: 
            self.command()

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
        self.root.title("Gestor Chat TCP/UDP - Proyecto Final Redes")
        self.root.geometry("750x550")
        self.root.configure(bg=COLOR_FONDO)
        self.root.minsize(650, 450)
        
        # Variables de estado
        self.proceso_servidor = None
        self.hilo_lectura = None
        self.protocolo = "TCP"
        self.cola_logs = queue.Queue()
        
        # Inicializar txt_consola como None
        self.txt_consola = None

        self.construir_interfaz()
        self.centrar_ventana()

    def construir_interfaz(self):
        """Construye todos los componentes de la interfaz."""
        # --- CONTENEDOR PRINCIPAL ---
        frame_main = tk.Frame(self.root, bg=COLOR_FONDO)
        frame_main.pack(fill="both", expand=True, padx=20, pady=15)

        # 1. TÍTULO Y AUTOR
        tk.Label(frame_main, text="Gestor Chat TCP/UDP", font=FONT_TITULO,
                 bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(pady=(0, 2))
        
        tk.Label(frame_main, 
                 text="Por: Ricardo Cervantes - Proyecto Final Redes 2025", 
                 font=FONT_SUBTITULO, bg=COLOR_FONDO, fg=COLOR_SUBTITULO).pack(pady=(0, 15))

        # 2. SELECTOR DE PROTOCOLO
        frame_proto = tk.Frame(frame_main, bg=COLOR_FONDO)
        frame_proto.pack(pady=(0, 10))

        tk.Label(frame_proto, text="Protocolo:", font=FONT_TEXTO, 
                 bg=COLOR_FONDO, fg=COLOR_SUBTITULO).pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_tcp = BotonRedondo(frame_proto, 90, 40, 15, "TCP", 
                                   command=lambda: self.set_protocolo("TCP"))
        self.btn_tcp.pack(side=tk.LEFT, padx=5)
        
        self.btn_udp = BotonRedondo(frame_proto, 90, 40, 15, "UDP", 
                                   command=lambda: self.set_protocolo("UDP"))
        self.btn_udp.pack(side=tk.LEFT, padx=5)

        self.set_protocolo("TCP")

        # 3. BOTONES DE CONTROL
        frame_botones = tk.Frame(frame_main, bg=COLOR_FONDO)
        frame_botones.pack(pady=(0, 15))

        self.btn_servidor = BotonRedondo(frame_botones, 220, 45, 20, 
                                        "INICIAR SERVIDOR", 
                                        bg_color=COLOR_BTN_ON, 
                                        command=self.toggle_servidor)
        self.btn_servidor.pack(side=tk.LEFT, padx=5)
        
        self.btn_cliente = BotonRedondo(frame_botones, 220, 45, 20, 
                                       "ABRIR CLIENTE GUI", 
                                       bg_color=COLOR_ACCENT_TCP, 
                                       command=self.abrir_cliente)
        self.btn_cliente.pack(side=tk.LEFT, padx=5)
        self.btn_cliente.set_disabled(True)
        
        self.btn_cliente_cli = BotonRedondo(frame_botones, 150, 45, 20,
                                           "CLIENTE CLI",
                                           bg_color="#6E7681",
                                           command=self.abrir_cliente_cli)
        self.btn_cliente_cli.pack(side=tk.LEFT, padx=5)
        self.btn_cliente_cli.set_disabled(True)

        # 4. INFORMACIÓN DEL SISTEMA
        frame_info = tk.Frame(frame_main, bg="#111111", bd=1, relief=tk.FLAT)
        frame_info.pack(fill="x", pady=(0, 15))

        info_text = """• Puerto: 5000
• Máximo clientes: 5
• Conectar a: 127.0.0.1:5000
• Mensaje privado: /p usuario mensaje
• Para salir: /salir
• Protocolo actual: TCP"""

        tk.Label(frame_info, text=info_text, font=("Consolas", 9), 
                 bg="#111111", fg="#CCCCCC", justify=tk.LEFT, 
                 padx=15, pady=10).pack()

        # 5. CONSOLA DE LOGS
        tk.Label(frame_main, text="LOGS DEL SISTEMA:", 
                 font=("Segoe UI", 9, "bold"),
                 bg=COLOR_FONDO, fg="#666666", anchor="w").pack(fill="x", pady=(0, 5))

        # CREAR txt_consola AQUÍ - ¡ESTO ES IMPORTANTE!
        self.txt_consola = scrolledtext.ScrolledText(
            frame_main, bg=COLOR_CONSOLA, fg="#00FF00",
            font=FONT_CONSOLA, bd=0, highlightthickness=0,
            wrap=tk.WORD
        )
        self.txt_consola.pack(fill="both", expand=True)
        self.txt_consola.config(state=tk.DISABLED)
        
        # Configurar tags para colores
        self.txt_consola.tag_config("config", foreground="#58A6FF")
        self.txt_consola.tag_config("error", foreground=COLOR_BTN_ALERT)
        self.txt_consola.tag_config("ok", foreground=COLOR_SISTEMA)

        # Iniciar verificación periódica de logs
        self.revisar_cola_logs()

    def centrar_ventana(self):
        """Centra la ventana en la pantalla."""
        self.root.update_idletasks()
        ancho = self.root.winfo_width()
        alto = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.root.winfo_screenheight() // 2) - (alto // 2)
        self.root.geometry(f'{ancho}x{alto}+{x}+{y}')

    def set_protocolo(self, proto):
        """
        Cambia el protocolo seleccionado.
        
        Args:
            proto: "TCP" o "UDP"
        """
        if self.proceso_servidor: 
            self.log("[INFO] No se puede cambiar protocolo con servidor activo")
            return
        
        self.protocolo = proto
        if proto == "TCP":
            self.btn_tcp.set_color(COLOR_ACCENT_TCP)
            self.btn_tcp.set_text("✓ TCP")
            self.btn_udp.set_color(COLOR_BTN_OFF)
            self.btn_udp.set_text("UDP")
            self.log(f"[CONFIG] Protocolo cambiado a TCP")
        else:
            self.btn_udp.set_color(COLOR_ACCENT_TCP)
            self.btn_udp.set_text("✓ UDP")
            self.btn_tcp.set_color(COLOR_BTN_OFF)
            self.btn_tcp.set_text("TCP")
            self.log(f"[CONFIG] Protocolo cambiado a UDP")

    def log(self, mensaje):
        """
        Agrega un mensaje a la consola de logs.
        
        Args:
            mensaje: Texto a mostrar
        """
        # Verificar que txt_consola existe
        if self.txt_consola is None:
            print(f"ERROR: txt_consola no inicializado. Mensaje: {mensaje}")
            return
            
        try:
            self.txt_consola.config(state=tk.NORMAL)
            
            # Agregar timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Determinar tag según contenido
            if "[ERROR]" in mensaje:
                tag = "error"
            elif "[CONFIG]" in mensaje:
                tag = "config"
            elif "[OK]" in mensaje or "correctamente" in mensaje:
                tag = "ok"
            else:
                tag = ""
            
            self.txt_consola.insert(tk.END, f"[{timestamp}] {mensaje}\n", tag)
            self.txt_consola.see(tk.END)  # Auto-scroll
            self.txt_consola.config(state=tk.DISABLED)
            
        except Exception as e:
            print(f"Error en log(): {e}")

    def revisar_cola_logs(self):
        """Revisa periódicamente la cola de logs del servidor."""
        try:
            while not self.cola_logs.empty():
                mensaje = self.cola_logs.get_nowait()
                self.log(mensaje)
        except:
            pass
        
        # Programar próxima revisión
        self.root.after(100, self.revisar_cola_logs)

    def leer_output_servidor(self, proceso):
        """
        Lee la salida del proceso del servidor.
        
        Args:
            proceso: Objeto subprocess.Popen del servidor
        """
        try:
            for linea in iter(proceso.stdout.readline, ''):
                if linea: 
                    self.cola_logs.put(linea.strip())
                else: 
                    break
        except:
            pass

    def toggle_servidor(self):
        """Inicia o detiene el servidor."""
        if self.proceso_servidor is None:
            self.iniciar_servidor()
        else:
            self.detener_servidor()

    def iniciar_servidor(self):
        """Inicia el servidor en el protocolo seleccionado."""
        self.log(f"=" * 50)
        self.log(f"Iniciando servidor {self.protocolo}...")
        
        try:
            # Comando para ejecutar servidor
            cmd_serv = [sys.executable, '-u', 'servidor.py', self.protocolo]
            
            # Flags para evitar ventana de consola en Windows
            flags = 0
            if os.name == 'nt':
                flags = subprocess.CREATE_NO_WINDOW
            
            # Ejecutar servidor como subproceso
            self.proceso_servidor = subprocess.Popen(
                cmd_serv, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True, 
                bufsize=1,
                creationflags=flags,
                encoding='utf-8'
            )

            # Hilo para leer logs del servidor
            self.hilo_lectura = threading.Thread(
                target=self.leer_output_servidor, 
                args=(self.proceso_servidor,), 
                daemon=True
            )
            self.hilo_lectura.start()

            # Actualizar interfaz
            self.btn_servidor.set_text("DETENER SERVIDOR")
            self.btn_servidor.set_color(COLOR_BTN_ALERT)
            self.btn_tcp.set_disabled(True)
            self.btn_udp.set_disabled(True)
            self.btn_cliente.set_disabled(False)
            self.btn_cliente_cli.set_disabled(False)
            
            self.log(f"[OK] Servidor {self.protocolo} iniciado")
            self.log(f"[INFO] Conectar clientes a: 127.0.0.1:5000")
            self.log(f"[INFO] Usa 'ABRIR CLIENTE GUI' para probar")
            
            # Verificar estado después de 2 segundos
            self.root.after(2000, self.verificar_servidor)
            
        except Exception as e:
            self.log(f"[ERROR] No se pudo iniciar servidor: {e}")
            self.proceso_servidor = None

    def verificar_servidor(self):
        """Verifica si el servidor sigue en ejecución."""
        if self.proceso_servidor:
            # Verificar si el proceso terminó
            retcode = self.proceso_servidor.poll()
            if retcode is not None:
                self.log(f"[ERROR] Servidor terminó con código: {retcode}")
                self.proceso_servidor = None
                self.restaurar_interfaz()
            else:
                # Volver a verificar en 5 segundos
                self.root.after(5000, self.verificar_servidor)

    def detener_servidor(self):
        """Detiene el servidor en ejecución."""
        self.log("Deteniendo servidor...")
        
        try:
            if self.proceso_servidor:
                self.log("Enviando señal de terminación...")
                
                if os.name == 'nt':  # Windows
                    subprocess.call(['taskkill', '/F', '/T', '/PID', 
                                   str(self.proceso_servidor.pid)])
                else:  # Linux/Mac
                    os.kill(self.proceso_servidor.pid, signal.SIGTERM)
                
                # Esperar a que termine
                self.proceso_servidor.wait(timeout=5)
                
            self.proceso_servidor = None
            self.log("[OK] Servidor detenido")
            
        except subprocess.TimeoutExpired:
            self.log("[ERROR] Timeout al detener servidor")
        except Exception as e:
            self.log(f"[ERROR] Error al detener servidor: {e}")
        finally:
            self.restaurar_interfaz()

    def restaurar_interfaz(self):
        """Restaura la interfaz al estado inicial."""
        self.btn_servidor.set_text("INICIAR SERVIDOR")
        self.btn_servidor.set_color(COLOR_BTN_ON)
        self.btn_tcp.set_disabled(False)
        self.btn_udp.set_disabled(False)
        self.btn_cliente.set_disabled(True)
        self.btn_cliente_cli.set_disabled(True)
        self.set_protocolo(self.protocolo)

    def abrir_cliente(self):
        """Abre la interfaz gráfica del cliente."""
        try:
            self.log("Abriendo cliente GUI...")
            
            # Verificar que existe el archivo
            archivo_cliente = 'guicliente.py'
            if not os.path.exists(archivo_cliente):
                self.log(f"[ERROR] No se encontró {archivo_cliente}")
                return
            
            # Ejecutar cliente
            cmd_cliente = [sys.executable, archivo_cliente]
            
            if os.name == 'nt':  # Windows
                # Crear nueva ventana de consola
                subprocess.Popen(cmd_cliente, creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:  # Linux/Mac
                # Ejecutar en terminal separado
                subprocess.Popen(['xterm', '-e', 'python', 'guicliente.py'])
            
            self.log("[OK] Cliente GUI abierto")
            self.log("[INFO] Configura conexión a 127.0.0.1:5000")
            
        except Exception as e:
            self.log(f"[ERROR] No se pudo abrir cliente: {e}")

    def abrir_cliente_cli(self):
        """Abre el cliente de línea de comandos."""
        try:
            self.log("Abriendo cliente CLI...")
            
            # Verificar que existe el archivo
            archivo_cliente = 'client.py'
            if not os.path.exists(archivo_cliente):
                self.log(f"[ERROR] No se encontró {archivo_cliente}")
                return
            
            # Ejecutar cliente
            cmd_cliente = [sys.executable, archivo_cliente]
            
            if os.name == 'nt':  # Windows
                subprocess.Popen(cmd_cliente, creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:  # Linux/Mac
                subprocess.Popen(['xterm', '-e', 'python', 'client.py'])
            
            self.log("[OK] Cliente CLI abierto")
            self.log(f"[INFO] Usa: 127.0.0.1:5000, protocolo: {self.protocolo}")
            
        except Exception as e:
            self.log(f"[ERROR] No se pudo abrir cliente CLI: {e}")

    def on_closing(self):
        """Maneja el cierre de la ventana principal."""
        if self.proceso_servidor:
            import tkinter.messagebox as mb
            respuesta = mb.askyesno(
                "Servidor Activo", 
                "El servidor está en ejecución.\n\n" +
                "¿Deseas detenerlo y salir?"
            )
            
            if respuesta:
                self.detener_servidor()
                self.root.destroy()
            else:
                return  # Cancelar cierre
        else:
            self.root.destroy()


if __name__ == "__main__":
    # Crear ventana principal
    root = tk.Tk()
    app = GestorChat(root)
    
    # Configurar manejo de cierre
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Iniciar aplicación
    root.mainloop()
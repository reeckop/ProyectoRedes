"""
Cliente GUI para chat TCP/UDP
Interfaz gráfica moderna con tkinter
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import socket
import threading
import comun
import time

# --- PALETA DE COLORES (Estilo VS Code) ---
COLOR_FONDO = "#1E1E1E"
COLOR_CHAT_BG = "#111111"
COLOR_TEXTO = "#F0F0F0"
COLOR_PROPIO = "#007ACC"      # Azul - mis mensajes
COLOR_AJENO = "#DDDDDD"       # Blanco - mensajes de otros
COLOR_SISTEMA = "#238636"     # Verde - mensajes del sistema
COLOR_ERROR = "#DA3633"       # Rojo - errores
COLOR_PRIVADO = "#E06C75"     # Rosa - mensajes privados

FONT_MAIN = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_MONO = ("Consolas", 9)

class ClienteChat:
    def __init__(self, root):
        self.root = root
        self.root.title("Cliente Chat TCP/UDP")
        self.root.geometry("550x650")
        self.root.configure(bg=COLOR_FONDO)
        self.root.minsize(500, 600)
        
        # Variables de conexión
        self.sock = None
        self.es_tcp = True
        self.nombre = ""
        self.host = "127.0.0.1"
        self.puerto = 5000
        self.conectado = False
        self.detener_hilo = False
        
        # Crear interfaz inicial
        self.crear_interfaz_login()
        
    def crear_interfaz_login(self):
        """Crea la interfaz de login/conección."""
        self.frame_login = tk.Frame(self.root, bg=COLOR_FONDO)
        self.frame_login.pack(expand=True, fill="both", padx=40, pady=40)

        # Título
        tk.Label(self.frame_login, text="CHAT TCP/UDP", 
                 font=("Segoe UI", 18, "bold"), 
                 bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(pady=(0, 30))

        # Nombre de usuario
        tk.Label(self.frame_login, text="Nombre de usuario:", 
                 font=FONT_MAIN, bg=COLOR_FONDO, fg="#AAAAAA").pack(anchor="w")
        self.entry_nombre = tk.Entry(self.frame_login, font=FONT_MAIN, 
                                    bg="#333333", fg="white", 
                                    insertbackground="white", width=30)
        self.entry_nombre.pack(fill="x", pady=(5, 15))
        self.entry_nombre.focus()

        # IP del servidor
        tk.Label(self.frame_login, text="IP del servidor:", 
                 font=FONT_MAIN, bg=COLOR_FONDO, fg="#AAAAAA").pack(anchor="w")
        self.entry_ip = tk.Entry(self.frame_login, font=FONT_MAIN, 
                                bg="#333333", fg="white", 
                                insertbackground="white", width=30)
        self.entry_ip.insert(0, "127.0.0.1")
        self.entry_ip.pack(fill="x", pady=(5, 15))
        
        # Puerto
        tk.Label(self.frame_login, text="Puerto:", 
                 font=FONT_MAIN, bg=COLOR_FONDO, fg="#AAAAAA").pack(anchor="w")
        self.entry_puerto = tk.Entry(self.frame_login, font=FONT_MAIN, 
                                    bg="#333333", fg="white", 
                                    insertbackground="white", width=30)
        self.entry_puerto.insert(0, "5000")
        self.entry_puerto.pack(fill="x", pady=(5, 15))
        
        # Protocolo
        tk.Label(self.frame_login, text="Protocolo:", 
                 font=FONT_MAIN, bg=COLOR_FONDO, fg="#AAAAAA").pack(anchor="w")
        
        self.var_proto = tk.StringVar(value="TCP")
        frame_proto = tk.Frame(self.frame_login, bg=COLOR_FONDO)
        frame_proto.pack(pady=5)
        
        tk.Radiobutton(frame_proto, text="TCP", variable=self.var_proto, 
                       value="TCP", bg=COLOR_FONDO, fg=COLOR_TEXTO, 
                       selectcolor="#000000", font=FONT_MAIN,
                       activebackground=COLOR_FONDO).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(frame_proto, text="UDP", variable=self.var_proto, 
                       value="UDP", bg=COLOR_FONDO, fg=COLOR_TEXTO, 
                       selectcolor="#000000", font=FONT_MAIN,
                       activebackground=COLOR_FONDO).pack(side=tk.LEFT, padx=10)

        # Botón conectar
        btn_conectar = tk.Button(self.frame_login, text="CONECTAR", 
                                font=FONT_BOLD, bg=COLOR_SISTEMA, fg=COLOR_TEXTO,
                                bd=0, padx=30, pady=10, 
                                activebackground="#2ea043",
                                command=self.conectar)
        btn_conectar.pack(pady=30)
        
        # Información
        tk.Label(self.frame_login, 
                 text="Conectarse a un servidor de chat TCP/UDP", 
                 font=("Segoe UI", 9), bg=COLOR_FONDO, fg="#666666").pack()

    def crear_interfaz_chat(self):
        """Crea la interfaz principal del chat."""
        self.frame_login.destroy()
        
        self.frame_chat = tk.Frame(self.root, bg=COLOR_FONDO)
        self.frame_chat.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Encabezado con información de conexión
        header = tk.Frame(self.frame_chat, bg="#111111", height=40)
        header.pack(fill="x", pady=(0, 10))
        header.pack_propagate(False)
        
        lbl_info = tk.Label(header, 
                           text=f"💬 {self.nombre} @ {self.host}:{self.puerto} ({self.var_proto.get()})", 
                           font=FONT_BOLD, bg="#111111", fg=COLOR_TEXTO)
        lbl_info.pack(side=tk.LEFT, padx=15, pady=10)
        
        btn_desconectar = tk.Button(header, text="Desconectar", 
                                   font=FONT_MAIN, bg=COLOR_ERROR, fg=COLOR_TEXTO,
                                   bd=0, padx=15, pady=5,
                                   activebackground="#c93c37",
                                   command=self.desconectar)
        btn_desconectar.pack(side=tk.RIGHT, padx=15, pady=5)

        # Área de chat con scroll
        frame_chat_area = tk.Frame(self.frame_chat, bg=COLOR_FONDO)
        frame_chat_area.pack(expand=True, fill="both", pady=(0, 10))
        
        self.txt_chat = scrolledtext.ScrolledText(
            frame_chat_area, 
            bg=COLOR_CHAT_BG, fg=COLOR_TEXTO, 
            font=FONT_MONO, bd=0, padx=15, pady=15,
            wrap=tk.WORD
        )
        self.txt_chat.pack(expand=True, fill="both")
        self.txt_chat.config(state=tk.DISABLED)
        
        # Configurar colores para diferentes tipos de mensajes
        self.txt_chat.tag_config("propio", foreground=COLOR_PROPIO)
        self.txt_chat.tag_config("ajeno", foreground=COLOR_AJENO)
        self.txt_chat.tag_config("privado", foreground=COLOR_PRIVADO)
        self.txt_chat.tag_config("sistema", foreground=COLOR_SISTEMA)
        self.txt_chat.tag_config("error", foreground=COLOR_ERROR)

        # Área de entrada de mensajes
        frame_input = tk.Frame(self.frame_chat, bg=COLOR_FONDO)
        frame_input.pack(fill="x")

        # Campo de entrada
        self.entry_msg = tk.Entry(frame_input, font=FONT_MAIN, 
                                 bg="#333333", fg="white", 
                                 insertbackground="white")
        self.entry_msg.pack(side=tk.LEFT, fill="x", expand=True, 
                           ipady=8, padx=(0, 10))
        self.entry_msg.bind("<Return>", lambda e: self.enviar_mensaje())
        self.entry_msg.focus()

        # Botón enviar
        btn_enviar = tk.Button(frame_input, text="Enviar", 
                              font=FONT_MAIN, bg=COLOR_PROPIO, fg=COLOR_TEXTO,
                              bd=0, padx=20, pady=8,
                              activebackground="#0066b3",
                              command=self.enviar_mensaje)
        btn_enviar.pack(side=tk.RIGHT)

        # Información de comandos
        frame_comandos = tk.Frame(self.frame_chat, bg=COLOR_FONDO)
        frame_comandos.pack(fill="x", pady=(10, 0))
        
        tk.Label(frame_comandos, 
                 text="Comandos: /p usuario mensaje (privado) | /salir (salir)", 
                 font=("Segoe UI", 8), bg=COLOR_FONDO, fg="#666666").pack()

    def agregar_mensaje(self, usuario, texto, tipo="PUBLICO", hora="--:--"):
        """
        Agrega un mensaje al área de chat.
        
        Args:
            usuario: Nombre del usuario
            texto: Contenido del mensaje
            tipo: Tipo de mensaje (PUBLICO, PRIVADO, SISTEMA, ERROR)
            hora: Hora del mensaje
        """
        self.txt_chat.config(state=tk.NORMAL)
        
        # Determinar etiqueta de color y formato
        if tipo == "ERROR":
            display_text = f"[{hora}] [ERROR] {texto}"
            tag = "error"
        elif tipo == "SISTEMA":
            display_text = f"[{hora}] [SISTEMA] {texto}"
            tag = "sistema"
        elif tipo == "PRIVADO":
            if usuario == self.nombre:
                # Mensaje privado enviado por mí
                if " a " in texto:
                    partes = texto.split(" a ", 1)
                    if len(partes) == 2:
                        display_text = f"[{hora}] [PRIVADO a {partes[0]}] {partes[1]}"
                    else:
                        display_text = f"[{hora}] [PRIVADO] {texto}"
                else:
                    display_text = f"[{hora}] [PRIVADO] {texto}"
            else:
                # Mensaje privado recibido
                display_text = f"[{hora}] [PRIVADO de {usuario}] {texto}"
            tag = "privado"
        elif usuario == self.nombre:
            # Mi mensaje público
            display_text = f"[{hora}] {usuario}: {texto}"
            tag = "propio"
        else:
            # Mensaje público de otro
            display_text = f"[{hora}] {usuario}: {texto}"
            tag = "ajeno"
        
        # Insertar mensaje
        self.txt_chat.insert(tk.END, display_text + "\n", tag)
        self.txt_chat.see(tk.END)  # Auto-scroll al final
        self.txt_chat.config(state=tk.DISABLED)

    def conectar(self):
        """Establece conexión con el servidor."""
        # Obtener datos del formulario
        self.nombre = self.entry_nombre.get().strip()
        self.host = self.entry_ip.get().strip()
        
        try:
            self.puerto = int(self.entry_puerto.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Puerto inválido. Debe ser un número.")
            return

        # Validaciones
        if not self.nombre:
            messagebox.showerror("Error", "Ingresa un nombre de usuario.")
            return
        
        if len(self.nombre) > 20:
            messagebox.showerror("Error", "El nombre no puede tener más de 20 caracteres.")
            return

        self.es_tcp = (self.var_proto.get() == "TCP")
        
        try:
            # Crear socket según protocolo
            if self.es_tcp:
                self.sock = comun.crear_socket_tcp()
                self.sock.connect((self.host, self.puerto))
            else:
                self.sock = comun.crear_socket_udp()
            
            # Enviar registro al servidor
            registro = comun.empaquetar_mensaje("REGISTRO", self.nombre, "Conectándose...")
            if self.es_tcp:
                self.sock.send(registro)
            else:
                self.sock.sendto(registro, (self.host, self.puerto))
            
            # Cambiar estado
            self.conectado = True
            self.detener_hilo = False
            
            # Iniciar hilo para recibir mensajes
            threading.Thread(target=self.recibir_mensajes, daemon=True).start()
            
            # Cambiar a interfaz de chat
            self.crear_interfaz_chat()
            
            # Mensaje de bienvenida
            self.agregar_mensaje("SISTEMA", f"Conectado como {self.nombre}", "SISTEMA")
            self.agregar_mensaje("SISTEMA", f"Servidor: {self.host}:{self.puerto} ({self.var_proto.get()})", "SISTEMA")
            self.agregar_mensaje("SISTEMA", "Usa /p usuario mensaje para enviar mensajes privados", "SISTEMA")
            self.agregar_mensaje("SISTEMA", "Escribe /salir para desconectarte", "SISTEMA")

        except ConnectionRefusedError:
            messagebox.showerror("Error de conexión", 
                               f"No se pudo conectar a {self.host}:{self.puerto}\n"
                               "Verifica que el servidor esté ejecutándose.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo conectar: {str(e)}")

    def recibir_mensajes(self):
        """Hilo para recibir mensajes del servidor."""
        while self.conectado and not self.detener_hilo:
            try:
                if self.es_tcp:
                    # TCP: recv bloqueante
                    datos = self.sock.recv(comun.BUFSIZE)
                    if not datos:
                        break  # Conexión cerrada
                else:
                    # UDP: recvfrom con timeout
                    self.sock.settimeout(1.0)
                    try:
                        datos, _ = self.sock.recvfrom(comun.BUFSIZE)
                    except socket.timeout:
                        continue  # Timeout, volver a intentar
                    except:
                        break  # Error
                    finally:
                        self.sock.settimeout(None)

                # Procesar mensaje
                msg = comun.desempaquetar_mensaje(datos)
                if msg:
                    hora = msg.get('fecha', '').split(' ')[1] if 'fecha' in msg else '--:--'
                    
                    # Manejar errores críticos
                    if msg['tipo'] == "ERROR":
                        contenido = msg.get('contenido', '')
                        if "llena" in contenido or "en uso" in contenido:
                            self.root.after(0, lambda: messagebox.showerror("Error", contenido))
                            self.conectado = False
                            self.root.after(0, self.root.destroy)
                            break
                    
                    # Agregar mensaje a la interfaz
                    self.root.after(0, lambda: self.agregar_mensaje(
                        msg['usuario'], msg['contenido'], msg['tipo'], hora))
            
            except (ConnectionResetError, ConnectionAbortedError):
                break
            except Exception as e:
                print(f"Error en recibir_mensajes: {e}")
                break
        
        # Si todavía está conectado pero salió del bucle, hubo error
        if self.conectado:
            self.conectado = False
            self.root.after(0, lambda: self.mostrar_desconexion())

    def mostrar_desconexion(self):
        """Muestra mensaje de desconexión y cierra la ventana."""
        messagebox.showinfo("Desconectado", "Se ha perdido la conexión con el servidor.")
        self.root.destroy()

    def enviar_mensaje(self):
        """Envía un mensaje al servidor."""
        texto = self.entry_msg.get().strip()
        if not texto or not self.conectado:
            return
        
        self.entry_msg.delete(0, tk.END)  # Limpiar campo
        
        # Comando especial: salir
        if texto.lower() == "/salir":
            self.desconectar()
            return
        
        # Determinar tipo de mensaje
        tipo = "PUBLICO"
        destino = None
        contenido = texto
        
        if texto.startswith("/p "):
            partes = texto.split(" ", 2)
            if len(partes) >= 3:
                tipo = "PRIVADO"
                destino = partes[1]
                contenido = partes[2]
                # Mostrar inmediatamente en el chat
                self.agregar_mensaje(self.nombre, f"a {destino}: {contenido}", "PRIVADO")
            else:
                self.agregar_mensaje("SISTEMA", "Formato: /p usuario mensaje", "ERROR")
                return
        else:
            # Mostrar mensaje público inmediatamente
            hora_actual = time.strftime("%H:%M")
            self.agregar_mensaje(self.nombre, contenido, "PUBLICO", hora_actual)
        
        # Empacar y enviar mensaje
        paquete = comun.empaquetar_mensaje(tipo, self.nombre, contenido, destino)
        
        try:
            if self.es_tcp:
                self.sock.send(paquete)
            else:
                self.sock.sendto(paquete, (self.host, self.puerto))
        except Exception as e:
            self.agregar_mensaje("SISTEMA", f"Error al enviar mensaje: {str(e)}", "ERROR")
            
    def desconectar(self):
        """Desconecta del servidor y cierra la aplicación."""
        self.conectado = False
        self.detener_hilo = True
        
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        
        self.root.destroy()

    def on_closing(self):
        """Maneja el cierre de la ventana."""
        if self.conectado:
            if messagebox.askyesno("Desconectar", 
                                  "¿Estás seguro de que quieres desconectarte?"):
                self.desconectar()
        else:
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ClienteChat(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Centrar ventana
    root.update_idletasks()
    ancho = root.winfo_width()
    alto = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (ancho // 2)
    y = (root.winfo_screenheight() // 2) - (alto // 2)
    root.geometry(f'{ancho}x{alto}+{x}+{y}')
    
    root.mainloop()
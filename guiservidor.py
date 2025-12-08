"""
Servidor GUI para chat TCP/UDP
Interfaz gráfica para monitorear y controlar el servidor
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import socket
import threading
import sys
import time
import comun
from datetime import datetime

# --- PALETA DE COLORES ---
COLOR_FONDO = "#1E1E1E"
COLOR_CHAT_BG = "#111111"
COLOR_TEXTO = "#FFFFFF"
COLOR_SISTEMA = "#238636"
COLOR_ERROR = "#DA3633"
COLOR_BTN = "#2D2D2D"
COLOR_BTN_HOVER = "#3E3E3E"
COLOR_PROPIO = "#007ACC"
COLOR_AJENO = "#DDDDDD"

FONT_MAIN = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_MONO = ("Consolas", 9)

class ServidorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Servidor Chat TCP/UDP")
        self.root.geometry("900x700")
        self.root.configure(bg=COLOR_FONDO)
        self.root.minsize(800, 600)
        
        # Variables del servidor
        self.servidor = None
        self.es_tcp = True
        self.protocolo = "TCP"
        self.clientes = {}
        self.lock = threading.Lock()
        self.en_ejecucion = False
        self.hilos_clientes = []
        self.detener_hilos = False
        
        self.construir_interfaz()
        self.centrar_ventana()
        
    def centrar_ventana(self):
        """Centra la ventana en la pantalla."""
        self.root.update_idletasks()
        ancho = self.root.winfo_width()
        alto = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.root.winfo_screenheight() // 2) - (alto // 2)
        self.root.geometry(f'{ancho}x{alto}+{x}+{y}')
        
    def construir_interfaz(self):
        """Construye la interfaz gráfica del servidor."""
        # Frame principal
        frame_main = tk.Frame(self.root, bg=COLOR_FONDO)
        frame_main.pack(fill="both", expand=True, padx=15, pady=15)
        
        # 1. ENCABEZADO Y CONTROLES
        frame_header = tk.Frame(frame_main, bg=COLOR_FONDO)
        frame_header.pack(fill="x", pady=(0, 15))
        
        # Título
        tk.Label(frame_header, text="🖥️ SERVIDOR DE CHAT TCP/UDP", font=FONT_TITLE,
                bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(side=tk.LEFT)
        
        # Controles a la derecha
        frame_controles = tk.Frame(frame_header, bg=COLOR_FONDO)
        frame_controles.pack(side=tk.RIGHT)
        
        # Selector de protocolo
        tk.Label(frame_controles, text="Protocolo:", font=FONT_MAIN,
                bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(side=tk.LEFT, padx=(0, 5))
        
        self.var_proto = tk.StringVar(value="TCP")
        self.combo_proto = ttk.Combobox(frame_controles, textvariable=self.var_proto,
                                       values=["TCP", "UDP"], state="readonly", 
                                       width=10, font=FONT_MAIN)
        self.combo_proto.pack(side=tk.LEFT, padx=(0, 15))
        
        # Botón inicio/detención
        self.btn_iniciar = tk.Button(frame_controles, text="▶ INICIAR SERVIDOR", 
                                    font=FONT_BOLD, bg=COLOR_SISTEMA, fg=COLOR_TEXTO,
                                    bd=0, padx=20, pady=8, 
                                    activebackground="#2ea043",
                                    command=self.toggle_servidor)
        self.btn_iniciar.pack(side=tk.LEFT)
        
        # 2. ESTADÍSTICAS EN TIEMPO REAL
        frame_stats = tk.Frame(frame_main, bg="#111111", relief=tk.RIDGE, bd=1)
        frame_stats.pack(fill="x", pady=(0, 15))
        
        # Estadísticas en una fila
        stats_grid = tk.Frame(frame_stats, bg="#111111")
        stats_grid.pack(pady=10)
        
        # Clientes conectados
        self.lbl_clientes = tk.Label(stats_grid, text="👥 Clientes: 0/5", 
                                    font=FONT_BOLD, bg="#111111", fg=COLOR_TEXTO)
        self.lbl_clientes.grid(row=0, column=0, padx=20, pady=5)
        
        # Protocolo actual
        self.lbl_protocolo = tk.Label(stats_grid, text="🔌 Protocolo: TCP", 
                                     font=FONT_MAIN, bg="#111111", fg=COLOR_TEXTO)
        self.lbl_protocolo.grid(row=0, column=1, padx=20, pady=5)
        
        # Estado del servidor
        self.lbl_estado = tk.Label(stats_grid, text="⏹️ Estado: Detenido", 
                                  font=FONT_MAIN, bg="#111111", fg=COLOR_ERROR)
        self.lbl_estado.grid(row=0, column=2, padx=20, pady=5)
        
        # Puerto en uso
        self.lbl_puerto = tk.Label(stats_grid, text="🚪 Puerto: 5000", 
                                  font=FONT_MAIN, bg="#111111", fg=COLOR_TEXTO)
        self.lbl_puerto.grid(row=0, column=3, padx=20, pady=5)
        
        # 3. LISTA DE CLIENTES CONECTADOS
        frame_clientes = tk.LabelFrame(frame_main, text="👥 Clientes Conectados", 
                                      font=FONT_BOLD, bg=COLOR_FONDO, fg=COLOR_TEXTO,
                                      relief=tk.FLAT, bd=1)
        frame_clientes.pack(fill="x", pady=(0, 15))
        
        # Cabecera de la lista
        header_frame = tk.Frame(frame_clientes, bg="#111111")
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        tk.Label(header_frame, text="Usuario", font=FONT_BOLD, 
                bg="#111111", fg=COLOR_TEXTO, width=20).pack(side=tk.LEFT)
        tk.Label(header_frame, text="Dirección IP", font=FONT_BOLD, 
                bg="#111111", fg=COLOR_TEXTO, width=20).pack(side=tk.LEFT)
        tk.Label(header_frame, text="Protocolo", font=FONT_BOLD, 
                bg="#111111", fg=COLOR_TEXTO, width=15).pack(side=tk.LEFT)
        tk.Label(header_frame, text="Actividad", font=FONT_BOLD, 
                bg="#111111", fg=COLOR_TEXTO, width=15).pack(side=tk.LEFT)
        
        # Lista de clientes con scroll
        canvas_clientes = tk.Canvas(frame_clientes, bg=COLOR_CHAT_BG, height=120)
        scrollbar = tk.Scrollbar(frame_clientes, orient="vertical", 
                                command=canvas_clientes.yview)
        self.scrollable_frame = tk.Frame(canvas_clientes, bg=COLOR_CHAT_BG)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas_clientes.configure(scrollregion=canvas_clientes.bbox("all"))
        )
        
        canvas_clientes.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas_clientes.configure(yscrollcommand=scrollbar.set)
        
        canvas_clientes.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=(0, 10))
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=(0, 10))
        
        self.frame_lista_clientes = self.scrollable_frame
        
        # 4. CONSOLA DE LOGS
        frame_logs = tk.LabelFrame(frame_main, text="📝 Logs del Servidor", 
                                  font=FONT_BOLD, bg=COLOR_FONDO, fg=COLOR_TEXTO,
                                  relief=tk.FLAT, bd=1)
        frame_logs.pack(fill="both", expand=True)
        
        self.txt_logs = scrolledtext.ScrolledText(
            frame_logs, bg=COLOR_CHAT_BG, fg="#00FF00", 
            font=FONT_MONO, bd=0, wrap=tk.WORD, padx=10, pady=10
        )
        self.txt_logs.pack(fill="both", expand=True, padx=5, pady=5)
        self.txt_logs.config(state=tk.DISABLED)
        
        # Configurar tags para colores
        self.txt_logs.tag_config("error", foreground=COLOR_ERROR)
        self.txt_logs.tag_config("sistema", foreground=COLOR_SISTEMA)
        self.txt_logs.tag_config("conexion", foreground="#58A6FF")
        self.txt_logs.tag_config("mensaje", foreground="#DDDDDD")
        
    def log(self, mensaje, tipo="mensaje"):
        """
        Agrega un mensaje a la consola de logs.
        
        Args:
            mensaje: Texto a mostrar
            tipo: Tipo de mensaje (error, sistema, conexion, mensaje)
        """
        self.txt_logs.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Formatear mensaje según tipo
        if tipo == "error":
            log_text = f"[{timestamp}] [ERROR] {mensaje}\n"
            tag = "error"
        elif tipo == "sistema":
            log_text = f"[{timestamp}] [SISTEMA] {mensaje}\n"
            tag = "sistema"
        elif tipo == "conexion":
            log_text = f"[{timestamp}] [CONEXION] {mensaje}\n"
            tag = "conexion"
        else:
            log_text = f"[{timestamp}] {mensaje}\n"
            tag = "mensaje"
        
        self.txt_logs.insert(tk.END, log_text, tag)
        self.txt_logs.see(tk.END)
        self.txt_logs.config(state=tk.DISABLED)
        
        # También imprimir en consola (para depuración)
        print(log_text.strip())
    
    def actualizar_estadisticas(self):
        """Actualiza las estadísticas en la interfaz."""
        with self.lock:
            num_clientes = len(self.clientes)
            
        self.lbl_clientes.config(text=f"👥 Clientes: {num_clientes}/{comun.MAX_CLIENTES}")
        self.lbl_protocolo.config(text=f"🔌 Protocolo: {self.protocolo}")
        self.lbl_puerto.config(text=f"🚪 Puerto: {comun.PORT}")
        
        # Actualizar estado
        if self.en_ejecucion:
            self.lbl_estado.config(text="▶ Estado: Ejecutándose", fg=COLOR_SISTEMA)
        else:
            self.lbl_estado.config(text="⏹️ Estado: Detenido", fg=COLOR_ERROR)
    
    def actualizar_lista_clientes(self):
        """Actualiza la lista visual de clientes conectados."""
        # Limpiar lista anterior
        for widget in self.frame_lista_clientes.winfo_children():
            widget.destroy()
        
        with self.lock:
            for i, (usuario, info) in enumerate(self.clientes.items()):
                # Crear fila para cada cliente
                row_frame = tk.Frame(self.frame_lista_clientes, bg=COLOR_CHAT_BG)
                row_frame.grid(row=i, column=0, sticky="ew", padx=5, pady=2)
                
                # Nombre de usuario
                lbl_usuario = tk.Label(row_frame, text=usuario, font=FONT_MAIN,
                                      bg=COLOR_CHAT_BG, fg=COLOR_TEXTO, width=20)
                lbl_usuario.pack(side=tk.LEFT, padx=(10, 0))
                
                # Dirección IP
                addr = info.get('addr', ('Desconocido', 0))
                ip_text = f"{addr[0]}:{addr[1]}" if addr != 'Desconocido' else "Desconocido"
                lbl_ip = tk.Label(row_frame, text=ip_text, font=FONT_MAIN,
                                 bg=COLOR_CHAT_BG, fg=COLOR_TEXTO, width=20)
                lbl_ip.pack(side=tk.LEFT)
                
                # Protocolo
                proto_text = "TCP" if self.es_tcp else "UDP"
                lbl_proto = tk.Label(row_frame, text=proto_text, font=FONT_MAIN,
                                    bg=COLOR_CHAT_BG, fg=COLOR_TEXTO, width=15)
                lbl_proto.pack(side=tk.LEFT)
                
                # Última actividad
                last_seen = info.get('last_seen', 0)
                if last_seen:
                    tiempo_transcurrido = time.time() - last_seen
                    if tiempo_transcurrido < 60:
                        actividad = f"Hace {int(tiempo_transcurrido)}s"
                    elif tiempo_transcurrido < 3600:
                        actividad = f"Hace {int(tiempo_transcurrido/60)}min"
                    else:
                        actividad = f"Hace {int(tiempo_transcurrido/3600)}h"
                else:
                    actividad = "Activo"
                    
                lbl_act = tk.Label(row_frame, text=actividad, font=FONT_MAIN,
                                  bg=COLOR_CHAT_BG, fg=COLOR_TEXTO, width=15)
                lbl_act.pack(side=tk.LEFT)
    
    def toggle_servidor(self):
        """Inicia o detiene el servidor."""
        if not self.en_ejecucion:
            self.iniciar_servidor()
        else:
            self.detener_servidor()
    
    def iniciar_servidor(self):
        """Inicia el servidor con el protocolo seleccionado."""
        self.protocolo = self.var_proto.get()
        self.es_tcp = (self.protocolo == "TCP")
        
        try:
            # Crear socket del servidor
            if self.es_tcp:
                self.servidor = comun.crear_socket_tcp()
                self.servidor.bind((comun.HOST, comun.PORT))
                self.servidor.listen(5)
                
                self.log(f"Servidor TCP iniciado en {comun.HOST}:{comun.PORT}", "sistema")
                
                # Hilo para aceptar conexiones TCP
                self.hilo_aceptar = threading.Thread(target=self.aceptar_conexiones_tcp, 
                                                   daemon=True)
                self.hilo_aceptar.start()
            else:
                self.servidor = comun.crear_socket_udp()
                self.servidor.bind((comun.HOST, comun.PORT))
                
                self.log(f"Servidor UDP iniciado en {comun.HOST}:{comun.PORT}", "sistema")
                
                # Hilo para manejar mensajes UDP
                self.hilo_udp = threading.Thread(target=self.manejar_udp, daemon=True)
                self.hilo_udp.start()
            
            self.en_ejecucion = True
            self.detener_hilos = False
            
            # Actualizar interfaz
            self.btn_iniciar.config(text="⏹️ DETENER SERVIDOR", bg=COLOR_ERROR)
            self.combo_proto.config(state="disabled")
            
            ip_local = comun.obtener_ip_local()
            self.log("=" * 50, "sistema")
            self.log(f"Servidor {self.protocolo} INICIADO", "sistema")
            self.log(f"IP Local: {ip_local}", "sistema")
            self.log(f"Puerto: {comun.PORT}", "sistema")
            self.log(f"Máximo clientes: {comun.MAX_CLIENTES}", "sistema")
            self.log("Esperando conexiones...", "sistema")
            self.log("=" * 50, "sistema")
            
            # Iniciar actualizaciones periódicas
            self.actualizar_estadisticas()
            self.actualizar_periodicamente()
            
        except Exception as e:
            self.log(f"ERROR al iniciar servidor: {str(e)}", "error")
            messagebox.showerror("Error", f"No se pudo iniciar el servidor:\n{str(e)}")
    
    def actualizar_periodicamente(self):
        """Actualiza estadísticas y lista periódicamente."""
        if self.en_ejecucion:
            self.actualizar_estadisticas()
            self.actualizar_lista_clientes()
            self.root.after(1000, self.actualizar_periodicamente)
    
    def aceptar_conexiones_tcp(self):
        """Acepta conexiones TCP entrantes."""
        while self.en_ejecucion and not self.detener_hilos:
            try:
                conn, addr = self.servidor.accept()
                self.log(f"Nueva conexión TCP desde {addr}", "conexion")
                
                # Crear hilo para manejar cliente
                hilo_cliente = threading.Thread(target=self.manejar_cliente_tcp, 
                                              args=(conn, addr), daemon=True)
                hilo_cliente.start()
                self.hilos_clientes.append(hilo_cliente)
                
            except socket.timeout:
                continue
            except:
                break
    
    def manejar_cliente_tcp(self, conn, addr):
        """Maneja un cliente TCP conectado."""
        usuario = None
        
        try:
            # Primer mensaje debe ser REGISTRO
            conn.settimeout(5.0)  # Timeout para registro
            datos = conn.recv(comun.BUFSIZE)
            
            if not datos:
                conn.close()
                return
                
            msg = comun.desempaquetar_mensaje(datos)
            if not msg or msg.get('tipo') != "REGISTRO":
                conn.close()
                return
                
            usuario = msg.get('usuario')
            if not usuario:
                conn.close()
                return
            
            # Registrar cliente
            with self.lock:
                if usuario in self.clientes:
                    error_msg = comun.empaquetar_mensaje("ERROR", "SERVER", "Nombre en uso.")
                    conn.send(error_msg)
                    conn.close()
                    return
                
                if len(self.clientes) >= comun.MAX_CLIENTES:
                    error_msg = comun.empaquetar_mensaje("ERROR", "SERVER", "Sala llena.")
                    conn.send(error_msg)
                    conn.close()
                    return
                
                self.clientes[usuario] = {"addr": addr, "conn": conn, "last_seen": time.time()}
                self.log(f"Usuario registrado: {usuario}", "conexion")
            
            # Enviar confirmación
            confirmacion = comun.empaquetar_mensaje("SISTEMA", "SERVER", 
                                                  f"Bienvenido {usuario}!")
            conn.send(confirmacion)
            
            # Notificar a otros usuarios
            sistema_msg = comun.empaquetar_mensaje("SISTEMA", "SERVER", 
                                                 f"{usuario} se ha unido al chat.")
            self.broadcast(sistema_msg, usuario)
            
            # Restaurar timeout
            conn.settimeout(None)
            
            # Bucle principal para recibir mensajes
            while self.en_ejecucion and not self.detener_hilos:
                try:
                    datos = conn.recv(comun.BUFSIZE)
                    if not datos:
                        break
                    
                    self.procesar_mensaje(datos, addr, conn)
                    
                except socket.timeout:
                    continue
                except:
                    break
                
        except socket.timeout:
            self.log(f"Timeout en conexión TCP: {addr}", "error")
        except Exception as e:
            self.log(f"Error con cliente TCP: {str(e)}", "error")
        finally:
            # Cerrar conexión y limpiar
            if usuario:
                with self.lock:
                    if usuario in self.clientes:
                        del self.clientes[usuario]
                        self.log(f"Usuario desconectado: {usuario}", "conexion")
                        
                        # Notificar a otros usuarios
                        if self.en_ejecucion:
                            msg_desconexion = comun.empaquetar_mensaje("SISTEMA", "SERVER", 
                                                                     f"{usuario} ha abandonado el chat.")
                            self.broadcast(msg_desconexion)
            
            try:
                conn.close()
            except:
                pass
    
    def manejar_udp(self):
        """Maneja mensajes UDP."""
        while self.en_ejecucion and not self.detener_hilos:
            try:
                datos, addr = self.servidor.recvfrom(comun.BUFSIZE)
                self.procesar_mensaje(datos, addr, None)
            except socket.timeout:
                continue
            except:
                break
    
    def procesar_mensaje(self, datos, addr, conn=None):
        """Procesa un mensaje recibido."""
        msg = comun.desempaquetar_mensaje(datos)
        if not msg:
            return
        
        tipo = msg.get('tipo')
        usuario = msg.get('usuario')
        contenido = msg.get('contenido', '')
        
        with self.lock:
            # REGISTRO (solo para UDP, TCP se maneja separadamente)
            if tipo == "REGISTRO" and not self.es_tcp:
                if usuario in self.clientes:
                    error_msg = comun.empaquetar_mensaje("ERROR", "SERVER", "Nombre en uso.")
                    self.servidor.sendto(error_msg, addr)
                    return
                
                if len(self.clientes) >= comun.MAX_CLIENTES:
                    error_msg = comun.empaquetar_mensaje("ERROR", "SERVER", "Sala llena.")
                    self.servidor.sendto(error_msg, addr)
                    return
                
                self.clientes[usuario] = {"addr": addr, "last_seen": time.time()}
                self.log(f"Usuario registrado (UDP): {usuario}", "conexion")
                
                # Enviar confirmación
                confirmacion = comun.empaquetar_mensaje("SISTEMA", "SERVER", 
                                                      f"Bienvenido {usuario}!")
                self.servidor.sendto(confirmacion, addr)
                
                # Notificar a otros
                sistema_msg = comun.empaquetar_mensaje("SISTEMA", "SERVER", 
                                                     f"{usuario} se ha unido al chat.")
                self.broadcast(sistema_msg, usuario)
                return
            
            # Verificar que el usuario esté registrado
            if usuario not in self.clientes:
                return
            
            # Actualizar dirección para UDP
            if not self.es_tcp:
                self.clientes[usuario]['addr'] = addr
            
            # Actualizar timestamp
            self.clientes[usuario]['last_seen'] = time.time()
            
            # MENSAJE PÚBLICO
            if tipo == "PUBLICO":
                self.log(f"{usuario}: {contenido}")
                self.broadcast(datos, usuario)
            
            # MENSAJE PRIVADO
            elif tipo == "PRIVADO":
                destino = msg.get('destino')
                if destino in self.clientes:
                    self.log(f"Privado: {usuario} -> {destino}: {contenido}")
                    self.enviar_mensaje(datos, destino)
                else:
                    error_msg = comun.empaquetar_mensaje("ERROR", "SERVER", 
                                                       f"Usuario {destino} no existe.")
                    if self.es_tcp and conn:
                        conn.send(error_msg)
                    else:
                        self.servidor.sendto(error_msg, addr)
    
    def enviar_mensaje(self, datos, destino):
        """Envía un mensaje a un cliente específico."""
        try:
            with self.lock:
                if destino in self.clientes:
                    info = self.clientes[destino]
                    if self.es_tcp:
                        info['conn'].send(datos)
                    else:
                        self.servidor.sendto(datos, info['addr'])
        except:
            pass
    
    def broadcast(self, datos, excepto=None):
        """Envía un mensaje a todos los clientes excepto al especificado."""
        with self.lock:
            for usuario, info in self.clientes.items():
                if usuario != excepto:
                    try:
                        if self.es_tcp:
                            info['conn'].send(datos)
                        else:
                            self.servidor.sendto(datos, info['addr'])
                    except:
                        # Eliminar cliente si hay error
                        if usuario in self.clientes:
                            del self.clientes[usuario]
                            self.log(f"Error enviando a {usuario}, desconectado", "error")
    
    def detener_servidor(self):
        """Detiene el servidor."""
        self.detener_hilos = True
        self.en_ejecucion = False
        
        # Notificar a todos los clientes
        if self.clientes:
            msg_desconexion = comun.empaquetar_mensaje("SISTEMA", "SERVER", 
                                                     "Servidor detenido. Desconectando...")
            self.broadcast(msg_desconexion)
        
        # Cerrar conexiones con clientes
        with self.lock:
            for usuario, info in self.clientes.items():
                if self.es_tcp and 'conn' in info:
                    try:
                        info['conn'].close()
                    except:
                        pass
            self.clientes.clear()
        
        # Cerrar socket del servidor
        if self.servidor:
            try:
                self.servidor.close()
            except:
                pass
        
        # Actualizar interfaz
        self.btn_iniciar.config(text="▶ INICIAR SERVIDOR", bg=COLOR_SISTEMA)
        self.combo_proto.config(state="readonly")
        
        self.log("=" * 50, "sistema")
        self.log("Servidor DETENIDO", "sistema")
        self.log("=" * 50, "sistema")
        
        self.actualizar_estadisticas()
        self.actualizar_lista_clientes()
    
    def on_closing(self):
        """Maneja el cierre de la ventana."""
        if self.en_ejecucion:
            respuesta = messagebox.askyesno(
                "Confirmar", 
                "El servidor está en ejecución. ¿Deseas detenerlo y salir?"
            )
            if respuesta:
                self.detener_servidor()
                self.root.destroy()
            else:
                return  # Cancelar cierre
        else:
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ServidorGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Centrar ventana
    root.update_idletasks()
    ancho = root.winfo_width()
    alto = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (ancho // 2)
    y = (root.winfo_screenheight() // 2) - (alto // 2)
    root.geometry(f'{ancho}x{alto}+{x}+{y}')
    
    root.mainloop()
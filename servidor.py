"""
Servidor de chat TCP/UDP
Maneja múltiples clientes, mensajes públicos y privados
"""

import socket
import threading
import sys
import comun
import time

# Estructura para guardar clientes conectados
# TCP: {"nombre": {"addr": direccion, "conn": socket, "last_seen": timestamp}}
# UDP: {"nombre": {"addr": direccion, "last_seen": timestamp}}
clientes = {}
lock = threading.Lock()

def log(texto):
    """Imprime log en consola con flush forzado para GUI."""
    print(texto)
    sys.stdout.flush()

def enviar_a_cliente(datos, info_cliente, es_tcp, sock_servidor=None):
    """
    Envía datos a un cliente específico.
    
    Args:
        datos: Bytes a enviar
        info_cliente: Información del cliente
        es_tcp: True para TCP, False para UDP
        sock_servidor: Socket del servidor (para UDP)
    """
    try:
        if es_tcp:
            info_cliente['conn'].send(datos)
        else:
            if sock_servidor and 'addr' in info_cliente:
                sock_servidor.sendto(datos, info_cliente['addr'])
    except Exception as e:
        log(f"Error enviando a cliente: {e}")

def manejar_registro(usuario, addr, conn, es_tcp, sock_servidor):
    """
    Registra un nuevo usuario en el servidor.
    
    Returns:
        bool: True si registro exitoso, False si error
    """
    with lock:
        # Verificar si el usuario ya existe
        if usuario in clientes:
            error = comun.empaquetar_mensaje("ERROR", "SERVER", "Nombre de usuario ya está en uso.")
            if es_tcp:
                conn.send(error)
            else:
                sock_servidor.sendto(error, addr)
            return False
        
        # Verificar límite de clientes
        if len(clientes) >= comun.MAX_CLIENTES:
            error = comun.empaquetar_mensaje("ERROR", "SERVER", "Sala llena. Máximo 5 usuarios.")
            if es_tcp:
                conn.send(error)
            else:
                sock_servidor.sendto(error, addr)
            return False
        
        # Registrar nuevo cliente
        if es_tcp:
            clientes[usuario] = {"addr": addr, "conn": conn, "last_seen": time.time()}
        else:
            clientes[usuario] = {"addr": addr, "last_seen": time.time()}
        
        log(f"[+] Usuario registrado: {usuario} desde {addr}")
        
        # Notificar a todos los clientes existentes (excepto el nuevo)
        msg_bienvenida = comun.empaquetar_mensaje("SISTEMA", "SERVER", f"{usuario} se ha unido al chat.")
        for user, info in clientes.items():
            if user != usuario:
                enviar_a_cliente(msg_bienvenida, info, es_tcp, sock_servidor)
        
        # Enviar confirmación al nuevo usuario
        confirmacion = comun.empaquetar_mensaje("SISTEMA", "SERVER", 
                                              f"Bienvenido {usuario}! Hay {len(clientes)} usuarios conectados.")
        if es_tcp:
            conn.send(confirmacion)
        else:
            sock_servidor.sendto(confirmacion, addr)
        
        return True

def broadcast_mensaje(datos, usuario_remitente, es_tcp, sock_servidor):
    """
    Envía un mensaje a todos los clientes excepto al remitente.
    
    Args:
        datos: Mensaje a broadcast
        usuario_remitente: Usuario que envía el mensaje (no recibe)
        es_tcp: True para TCP, False para UDP
        sock_servidor: Socket del servidor (para UDP)
    """
    with lock:
        usuarios_a_eliminar = []
        for usuario, info in clientes.items():
            if usuario != usuario_remitente:
                try:
                    enviar_a_cliente(datos, info, es_tcp, sock_servidor)
                except:
                    usuarios_a_eliminar.append(usuario)
        
        # Eliminar clientes con error de envío
        for usuario in usuarios_a_eliminar:
            if usuario in clientes:
                del clientes[usuario]
                log(f"[-] Usuario eliminado (error envío): {usuario}")

def manejar_mensaje_publico(datos, usuario, es_tcp, sock_servidor):
    """
    Procesa un mensaje público y lo reenvía a todos.
    """
    with lock:
        if usuario not in clientes:
            return
        
        # Actualizar timestamp de actividad
        clientes[usuario]['last_seen'] = time.time()
        
        # Log en servidor
        msg_dict = comun.desempaquetar_mensaje(datos)
        if msg_dict:
            log(f"[PUBLICO] {usuario}: {msg_dict['contenido']}")
        
        # Reenviar a todos los demás
        broadcast_mensaje(datos, usuario, es_tcp, sock_servidor)

def manejar_mensaje_privado(msg_dict, datos, usuario, es_tcp, sock_servidor, addr, conn):
    """
    Procesa un mensaje privado entre dos usuarios.
    """
    destino = msg_dict.get('destino')
    
    with lock:
        if usuario not in clientes:
            return
        
        # Actualizar timestamp
        clientes[usuario]['last_seen'] = time.time()
        
        if destino in clientes:
            log(f"[PRIVADO] {usuario} -> {destino}")
            
            # Enviar mensaje al destino
            enviar_a_cliente(datos, clientes[destino], es_tcp, sock_servidor)
            
            # Confirmación al remitente
            confirmacion = comun.empaquetar_mensaje("SISTEMA", "SERVER", 
                                                  f"Mensaje privado enviado a {destino}")
            if es_tcp:
                conn.send(confirmacion)
            else:
                sock_servidor.sendto(confirmacion, addr)
        else:
            error = comun.empaquetar_mensaje("ERROR", "SERVER", 
                                           f"Usuario '{destino}' no encontrado.")
            if es_tcp:
                conn.send(error)
            else:
                sock_servidor.sendto(error, addr)

def manejar_cliente_tcp(conn, addr):
    """
    Maneja la conexión de un cliente TCP.
    """
    usuario_actual = None
    es_tcp = True
    
    try:
        # Primer mensaje debe ser REGISTRO
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
        
        # Intentar registro
        if not manejar_registro(usuario, addr, conn, es_tcp, None):
            conn.close()
            return
            
        usuario_actual = usuario
        
        # Bucle principal para recibir mensajes
        while True:
            datos = conn.recv(comun.BUFSIZE)
            if not datos:
                break
            
            msg = comun.desempaquetar_mensaje(datos)
            if not msg:
                continue
            
            tipo = msg.get('tipo')
            usuario = msg.get('usuario')
            
            # Verificar que el mensaje sea del usuario registrado
            if usuario == usuario_actual:
                if tipo == "PUBLICO":
                    manejar_mensaje_publico(datos, usuario, es_tcp, None)
                elif tipo == "PRIVADO":
                    manejar_mensaje_privado(msg, datos, usuario, es_tcp, None, addr, conn)
    
    except ConnectionResetError:
        log(f"Conexión TCP cerrada abruptamente: {addr}")
    except Exception as e:
        log(f"Error con cliente TCP {addr}: {e}")
    finally:
        # Limpiar desconexión
        if usuario_actual:
            with lock:
                if usuario_actual in clientes:
                    del clientes[usuario_actual]
                    log(f"[-] Usuario desconectado: {usuario_actual}")
                    
                    # Notificar a los demás usuarios
                    msg_desconexion = comun.empaquetar_mensaje("SISTEMA", "SERVER", 
                                                             f"{usuario_actual} ha abandonado el chat.")
                    for user, info in clientes.items():
                        enviar_a_cliente(msg_desconexion, info, es_tcp, None)
        
        try:
            conn.close()
        except:
            pass

def iniciar_servidor_tcp():
    """Inicia el servidor en modo TCP."""
    servidor = comun.crear_socket_tcp()
    
    try:
        servidor.bind((comun.HOST, comun.PORT))
        servidor.listen(5)
        
        ip_local = comun.obtener_ip_local()
        log("=" * 50)
        log(">>> SERVIDOR TCP INICIADO <<<")
        log(f"IP: {ip_local}")
        log(f"Puerto: {comun.PORT}")
        log(f"Máximo clientes: {comun.MAX_CLIENTES}")
        log("=" * 50)
        log("Esperando conexiones...")
        
        while True:
            conn, addr = servidor.accept()
            log(f"Nueva conexión TCP desde {addr}")
            hilo = threading.Thread(target=manejar_cliente_tcp, args=(conn, addr))
            hilo.daemon = True
            hilo.start()
    
    except KeyboardInterrupt:
        log("\n[!] Servidor detenido por el usuario.")
    except Exception as e:
        log(f"[ERROR] Error en servidor TCP: {e}")
    finally:
        servidor.close()

def iniciar_servidor_udp():
    """Inicia el servidor en modo UDP."""
    servidor = comun.crear_socket_udp()
    
    try:
        servidor.bind((comun.HOST, comun.PORT))
        
        ip_local = comun.obtener_ip_local()
        log("=" * 50)
        log(">>> SERVIDOR UDP INICIADO <<<")
        log(f"IP: {ip_local}")
        log(f"Puerto: {comun.PORT}")
        log(f"Máximo clientes: {comun.MAX_CLIENTES}")
        log("=" * 50)
        log("Esperando mensajes...")
        
        while True:
            datos, addr = servidor.recvfrom(comun.BUFSIZE)
            
            msg = comun.desempaquetar_mensaje(datos)
            if not msg:
                continue
            
            tipo = msg.get('tipo')
            usuario = msg.get('usuario')
            
            if not usuario:
                continue
            
            # REGISTRO
            if tipo == "REGISTRO":
                manejar_registro(usuario, addr, None, False, servidor)
            
            # MENSAJE PÚBLICO
            elif tipo == "PUBLICO":
                with lock:
                    if usuario in clientes:
                        # Actualizar dirección (UDP puede cambiar)
                        clientes[usuario]['addr'] = addr
                        clientes[usuario]['last_seen'] = time.time()
                        manejar_mensaje_publico(datos, usuario, False, servidor)
            
            # MENSAJE PRIVADO
            elif tipo == "PRIVADO":
                with lock:
                    if usuario in clientes:
                        clientes[usuario]['addr'] = addr
                        clientes[usuario]['last_seen'] = time.time()
                        manejar_mensaje_privado(msg, datos, usuario, False, servidor, addr, None)
    
    except KeyboardInterrupt:
        log("\n[!] Servidor detenido por el usuario.")
    except Exception as e:
        log(f"[ERROR] Error en servidor UDP: {e}")
    finally:
        servidor.close()

def iniciar_servidor():
    """
    Función principal para iniciar el servidor.
    Uso: python servidor.py [TCP/UDP]
    """
    protocolo = "TCP"
    if len(sys.argv) > 1:
        protocolo = sys.argv[1].upper()
    
    log(f"Iniciando servidor en modo {protocolo}...")
    
    if protocolo == "UDP":
        iniciar_servidor_udp()
    else:
        iniciar_servidor_tcp()

if __name__ == "__main__":
    iniciar_servidor()
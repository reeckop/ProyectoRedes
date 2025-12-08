"""
Módulo común para chat TCP/UDP
Funciones compartidas por servidor y cliente
"""

import socket
import json
from datetime import datetime

# --- CONFIGURACIÓN GLOBAL PARA AMBOS PROTOCOLOS ---
HOST = '0.0.0.0'  # Escuchar en todas las interfaces
PORT = 5000
BUFSIZE = 4096  # Aumentado para mensajes largos
MAX_CLIENTES = 5
CODIFICACION = 'utf-8'

def empaquetar_mensaje(tipo, usuario, contenido, destino=None):
    """
    Crea un diccionario con la estructura del mensaje y lo convierte a bytes.
    
    Args:
        tipo: "PUBLICO", "PRIVADO", "REGISTRO", "ERROR", "SISTEMA"
        usuario: Nombre del usuario que envía
        contenido: Texto del mensaje
        destino: Para mensajes privados, usuario destino
    
    Returns:
        bytes: Mensaje serializado en JSON
    """
    msg = {
        "tipo": tipo,
        "usuario": usuario,
        "contenido": contenido,
        "destino": destino,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    return json.dumps(msg).encode(CODIFICACION)

def desempaquetar_mensaje(datos):
    """
    Convierte bytes a diccionario.
    
    Args:
        datos: Bytes recibidos del socket
    
    Returns:
        dict: Mensaje deserializado o None si hay error
    """
    try:
        return json.loads(datos.decode(CODIFICACION))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

def obtener_ip_local():
    """
    Obtiene la IP local real de la máquina.
    
    Returns:
        str: IP local o "127.0.0.1" si hay error
    """
    try:
        # Método para obtener IP real (no localhost)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def crear_socket_tcp():
    """Crea y configura un socket TCP."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return sock

def crear_socket_udp():
    """Crea y configura un socket UDP."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return sock

def formatear_mensaje_para_mostrar(msg):
    """
    Formatea un mensaje para mostrar en consola/GUI.
    
    Args:
        msg: Diccionario del mensaje
    
    Returns:
        str: Mensaje formateado
    """
    if not msg:
        return ""
    
    hora = msg.get('fecha', '--:--').split(' ')[1] if 'fecha' in msg else '--:--'
    tipo = msg.get('tipo', '')
    usuario = msg.get('usuario', '')
    contenido = msg.get('contenido', '')
    
    if tipo == "ERROR":
        return f"[ERROR] {contenido}"
    elif tipo == "SISTEMA":
        return f"[SISTEMA] {contenido}"
    elif tipo == "PRIVADO":
        return f"[{hora}] (PRIVADO de {usuario}): {contenido}"
    else:
        return f"[{hora}] {usuario}: {contenido}"
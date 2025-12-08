import socket
import json
from datetime import datetime

# --- CONFIGURACION GLOBAL ---
# Cambia esto a socket.SOCK_DGRAM para UDP o socket.SOCK_STREAM para TCP
PROTOCOLO = socket.SOCK_STREAM 

# 0.0.0.0 significa "Escuchar en todas las interfaces de red de esta PC"
HOST = '0.0.0.0'
PORT = 5000
BUFSIZE = 1024
MAX_CLIENTES = 5

def empaquetar_mensaje(tipo, usuario, contenido, destino=None):
    """Crea un diccionario con la estructura del mensaje y lo convierte a bytes."""
    msg = {
        "tipo": tipo,  # PUBLICO, PRIVADO, REGISTRO, ERROR
        "usuario": usuario,
        "contenido": contenido,
        "destino": destino,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    return json.dumps(msg).encode('utf-8')

def desempaquetar_mensaje(datos):
    """Convierte bytes a diccionario."""
    try:
        return json.loads(datos.decode('utf-8'))
    except:
        return None
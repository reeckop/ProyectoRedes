"""
config.py - Módulo de configuración del chat
Permite cambiar fácilmente entre TCP y UDP
"""

# Configuración del servidor
HOST = 'localhost'
PORT = 5000

# Protocolo: 'TCP' o 'UDP'
PROTOCOL = 'TCP'

# Número máximo de clientes
MAX_CLIENTS = 5

# Tamaño del buffer
BUFFER_SIZE = 4096

# Códigos de mensaje
MSG_TYPES = {
    'REGISTER': 'REG',
    'REGISTER_OK': 'REG_OK',
    'REGISTER_FAIL': 'REG_FAIL',
    'BROADCAST': 'BROADCAST',
    'PRIVATE': 'PRIVATE',
    'LIST_USERS': 'LIST',
    'USER_LIST': 'USERS',
    'DISCONNECT': 'DISC',
    'SERVER_MSG': 'SERVER',
    'ERROR': 'ERROR'
}
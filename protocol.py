"""
protocol.py - Módulo de abstracción de protocolos TCP/UDP
Permite cambiar entre protocolos sin afectar la lógica del chat
"""

import socket
import json
from datetime import datetime
from config import HOST, PORT, PROTOCOL, BUFFER_SIZE

class Message:
    """Clase para estructurar los mensajes del chat"""
    def __init__(self, msg_type, sender="", content="", recipient=""):
        self.msg_type = msg_type
        self.sender = sender
        self.content = content
        self.recipient = recipient
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def to_json(self):
        return json.dumps({
            'type': self.msg_type,
            'sender': self.sender,
            'content': self.content,
            'recipient': self.recipient,
            'timestamp': self.timestamp
        })
    
    @staticmethod
    def from_json(json_str):
        data = json.loads(json_str)
        msg = Message(data['type'], data['sender'], data['content'], data.get('recipient', ''))
        msg.timestamp = data['timestamp']
        return msg
    
    def format_display(self):
        return f"[{self.timestamp}] {self.sender}: {self.content}"


class TCPServerSocket:
    """Socket servidor TCP"""
    def __init__(self, host=HOST, port=PORT):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((host, port))
        self.socket.listen(5)
        self.protocol = 'TCP'
    
    def accept_client(self):
        conn, addr = self.socket.accept()
        return TCPClientConnection(conn, addr)
    
    def close(self):
        self.socket.close()


class TCPClientConnection:
    """Conexión de cliente TCP (lado servidor)"""
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
    
    def receive(self):
        data = self.conn.recv(BUFFER_SIZE)
        if data:
            return Message.from_json(data.decode('utf-8'))
        return None
    
    def send(self, message):
        self.conn.send(message.to_json().encode('utf-8'))
    
    def close(self):
        self.conn.close()


class TCPClientSocket:
    """Socket cliente TCP"""
    def __init__(self, host=HOST, port=PORT):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.protocol = 'TCP'
    
    def connect(self):
        self.socket.connect((self.host, self.port))
    
    def send(self, message):
        self.socket.send(message.to_json().encode('utf-8'))
    
    def receive(self):
        data = self.socket.recv(BUFFER_SIZE)
        if data:
            return Message.from_json(data.decode('utf-8'))
        return None
    
    def close(self):
        self.socket.close()


class UDPServerSocket:
    """Socket servidor UDP"""
    def __init__(self, host=HOST, port=PORT):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((host, port))
        self.protocol = 'UDP'
        self.clients = {}  # addr -> username
    
    def receive_from(self):
        data, addr = self.socket.recvfrom(BUFFER_SIZE)
        if data:
            return Message.from_json(data.decode('utf-8')), addr
        return None, None
    
    def send_to(self, message, addr):
        self.socket.sendto(message.to_json().encode('utf-8'), addr)
    
    def close(self):
        self.socket.close()


class UDPClientSocket:
    """Socket cliente UDP"""
    def __init__(self, host=HOST, port=PORT):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', 0))  # Puerto aleatorio
        self.server_addr = (host, port)
        self.protocol = 'UDP'
    
    def connect(self):
        pass  # UDP no requiere conexión
    
    def send(self, message):
        self.socket.sendto(message.to_json().encode('utf-8'), self.server_addr)
    
    def receive(self):
        data, _ = self.socket.recvfrom(BUFFER_SIZE)
        if data:
            return Message.from_json(data.decode('utf-8'))
        return None
    
    def close(self):
        self.socket.close()


def create_server_socket(protocol=PROTOCOL):
    """Factory para crear socket servidor según protocolo"""
    if protocol == 'TCP':
        return TCPServerSocket()
    return UDPServerSocket()


def create_client_socket(protocol=PROTOCOL):
    """Factory para crear socket cliente según protocolo"""
    if protocol == 'TCP':
        return TCPClientSocket()
    return UDPClientSocket()
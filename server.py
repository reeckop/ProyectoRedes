"""
server.py - Servidor del chat TCP/UDP
Maneja múltiples clientes con hilos
"""

import threading
from config import PROTOCOL, MAX_CLIENTS, MSG_TYPES
from protocol import create_server_socket, Message

class ChatServer:
    def __init__(self):
        self.server_socket = create_server_socket(PROTOCOL)
        self.clients = {}  # TCP: {conn: username} | UDP: {addr: username}
        self.clients_lock = threading.Lock()
        self.running = True
        print(f"[SERVIDOR] Iniciado en modo {PROTOCOL}")
        print(f"[SERVIDOR] Máximo de clientes: {MAX_CLIENTS}")
    
    def broadcast(self, message, exclude=None):
        """Envía mensaje a todos los clientes conectados"""
        with self.clients_lock:
            if PROTOCOL == 'TCP':
                for conn, username in list(self.clients.items()):
                    if conn != exclude:
                        try:
                            conn.send(message)
                        except:
                            pass
            else:
                for addr, username in list(self.clients.items()):
                    if addr != exclude:
                        self.server_socket.send_to(message, addr)
    
    def send_private(self, message, recipient):
        """Envía mensaje privado a un usuario específico"""
        with self.clients_lock:
            if PROTOCOL == 'TCP':
                for conn, username in self.clients.items():
                    if username == recipient:
                        conn.send(message)
                        return True
            else:
                for addr, username in self.clients.items():
                    if username == recipient:
                        self.server_socket.send_to(message, addr)
                        return True
        return False
    
    def get_user_list(self):
        """Retorna lista de usuarios conectados"""
        with self.clients_lock:
            return list(self.clients.values())
    
    def register_client(self, client_id, username):
        """Registra un nuevo cliente"""
        with self.clients_lock:
            if len(self.clients) >= MAX_CLIENTS:
                return False, "Servidor lleno"
            if username in self.clients.values():
                return False, "Usuario ya existe"
            self.clients[client_id] = username
            return True, "Registro exitoso"
    
    def remove_client(self, client_id):
        """Elimina un cliente"""
        with self.clients_lock:
            if client_id in self.clients:
                username = self.clients.pop(client_id)
                return username
        return None

    def handle_tcp_client(self, client_conn):
        """Maneja un cliente TCP en un hilo separado"""
        username = None
        try:
            while self.running:
                msg = client_conn.receive()
                if not msg:
                    break
                
                if msg.msg_type == MSG_TYPES['REGISTER']:
                    success, reason = self.register_client(client_conn, msg.sender)
                    if success:
                        username = msg.sender
                        response = Message(MSG_TYPES['REGISTER_OK'], "Servidor", f"Bienvenido {username}!")
                        client_conn.send(response)
                        notify = Message(MSG_TYPES['SERVER_MSG'], "Servidor", f"{username} se ha conectado")
                        self.broadcast(notify, exclude=client_conn)
                        print(f"[+] {username} conectado. Total: {len(self.clients)}")
                    else:
                        response = Message(MSG_TYPES['REGISTER_FAIL'], "Servidor", reason)
                        client_conn.send(response)
                
                elif msg.msg_type == MSG_TYPES['BROADCAST']:
                    print(f"[BROADCAST] {msg.format_display()}")
                    self.broadcast(msg)
                
                elif msg.msg_type == MSG_TYPES['PRIVATE']:
                    print(f"[PRIVADO] {msg.sender} -> {msg.recipient}: {msg.content}")
                    if not self.send_private(msg, msg.recipient):
                        error = Message(MSG_TYPES['ERROR'], "Servidor", f"Usuario '{msg.recipient}' no encontrado")
                        client_conn.send(error)
                    else:
                        # Enviar copia al remitente
                        confirm = Message(MSG_TYPES['PRIVATE'], msg.sender, f"[Privado a {msg.recipient}]: {msg.content}")
                        client_conn.send(confirm)
                
                elif msg.msg_type == MSG_TYPES['LIST_USERS']:
                    users = ", ".join(self.get_user_list())
                    response = Message(MSG_TYPES['USER_LIST'], "Servidor", f"Conectados: {users}")
                    client_conn.send(response)
                
                elif msg.msg_type == MSG_TYPES['DISCONNECT']:
                    break
        
        except Exception as e:
            print(f"[ERROR] {e}")
        finally:
            if username:
                self.remove_client(client_conn)
                notify = Message(MSG_TYPES['SERVER_MSG'], "Servidor", f"{username} se ha desconectado")
                self.broadcast(notify)
                print(f"[-] {username} desconectado. Total: {len(self.clients)}")
            client_conn.close()

    def handle_udp(self):
        """Maneja todos los clientes UDP en un solo bucle"""
        print("[SERVIDOR UDP] Esperando mensajes...")
        while self.running:
            try:
                msg, addr = self.server_socket.receive_from()
                if not msg:
                    continue
                
                if msg.msg_type == MSG_TYPES['REGISTER']:
                    success, reason = self.register_client(addr, msg.sender)
                    if success:
                        response = Message(MSG_TYPES['REGISTER_OK'], "Servidor", f"Bienvenido {msg.sender}!")
                        self.server_socket.send_to(response, addr)
                        notify = Message(MSG_TYPES['SERVER_MSG'], "Servidor", f"{msg.sender} se ha conectado")
                        self.broadcast(notify, exclude=addr)
                        print(f"[+] {msg.sender} conectado. Total: {len(self.clients)}")
                    else:
                        response = Message(MSG_TYPES['REGISTER_FAIL'], "Servidor", reason)
                        self.server_socket.send_to(response, addr)
                
                elif msg.msg_type == MSG_TYPES['BROADCAST']:
                    print(f"[BROADCAST] {msg.format_display()}")
                    self.broadcast(msg)
                
                elif msg.msg_type == MSG_TYPES['PRIVATE']:
                    print(f"[PRIVADO] {msg.sender} -> {msg.recipient}: {msg.content}")
                    if not self.send_private(msg, msg.recipient):
                        error = Message(MSG_TYPES['ERROR'], "Servidor", f"Usuario '{msg.recipient}' no encontrado")
                        self.server_socket.send_to(error, addr)
                    else:
                        confirm = Message(MSG_TYPES['PRIVATE'], msg.sender, f"[Privado a {msg.recipient}]: {msg.content}")
                        self.server_socket.send_to(confirm, addr)
                
                elif msg.msg_type == MSG_TYPES['LIST_USERS']:
                    users = ", ".join(self.get_user_list())
                    response = Message(MSG_TYPES['USER_LIST'], "Servidor", f"Conectados: {users}")
                    self.server_socket.send_to(response, addr)
                
                elif msg.msg_type == MSG_TYPES['DISCONNECT']:
                    username = self.remove_client(addr)
                    if username:
                        notify = Message(MSG_TYPES['SERVER_MSG'], "Servidor", f"{username} se ha desconectado")
                        self.broadcast(notify)
                        print(f"[-] {username} desconectado. Total: {len(self.clients)}")
            
            except Exception as e:
                print(f"[ERROR UDP] {e}")

    def start(self):
        """Inicia el servidor"""
        try:
            if PROTOCOL == 'TCP':
                print("[SERVIDOR TCP] Esperando conexiones...")
                while self.running:
                    client_conn = self.server_socket.accept_client()
                    print(f"[CONEXIÓN] Nueva conexión desde {client_conn.addr}")
                    thread = threading.Thread(target=self.handle_tcp_client, args=(client_conn,))
                    thread.daemon = True
                    thread.start()
            else:
                self.handle_udp()
        except KeyboardInterrupt:
            print("\n[SERVIDOR] Cerrando...")
        finally:
            self.running = False
            self.server_socket.close()


if __name__ == "__main__":
    server = ChatServer()
    server.start()
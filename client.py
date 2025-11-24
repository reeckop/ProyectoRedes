"""
client.py - Cliente del chat TCP/UDP
Interfaz de línea de comandos con hilos para recibir y enviar
"""

import threading
import sys
from config import PROTOCOL, MSG_TYPES
from protocol import create_client_socket, Message

class ChatClient:
    def __init__(self):
        self.client_socket = create_client_socket(PROTOCOL)
        self.username = None
        self.running = True
        print(f"[CLIENTE] Modo {PROTOCOL}")
    
    def display_help(self):
        """Muestra comandos disponibles"""
        print("\n" + "="*50)
        print("COMANDOS DISPONIBLES:")
        print("  /msg <usuario> <mensaje> - Mensaje privado")
        print("  /usuarios                - Ver usuarios conectados")
        print("  /salir                   - Desconectarse")
        print("  /ayuda                   - Mostrar esta ayuda")
        print("  <mensaje>                - Enviar a todos")
        print("="*50 + "\n")
    
    def receive_messages(self):
        """Hilo para recibir mensajes del servidor"""
        while self.running:
            try:
                msg = self.client_socket.receive()
                if not msg:
                    if self.running:
                        print("\n[!] Conexión perdida con el servidor")
                    break
                
                if msg.msg_type == MSG_TYPES['REGISTER_FAIL']:
                    print(f"\n[ERROR] {msg.content}")
                    self.running = False
                    break
                elif msg.msg_type == MSG_TYPES['REGISTER_OK']:
                    print(f"\n[SERVIDOR] {msg.content}")
                    self.display_help()
                elif msg.msg_type == MSG_TYPES['BROADCAST']:
                    print(f"\n{msg.format_display()}")
                elif msg.msg_type == MSG_TYPES['PRIVATE']:
                    if msg.sender == self.username:
                        print(f"\n{msg.content}")
                    else:
                        print(f"\n[PRIVADO] {msg.format_display()}")
                elif msg.msg_type == MSG_TYPES['USER_LIST']:
                    print(f"\n[{msg.timestamp}] {msg.content}")
                elif msg.msg_type == MSG_TYPES['SERVER_MSG']:
                    print(f"\n[SERVIDOR] [{msg.timestamp}] {msg.content}")
                elif msg.msg_type == MSG_TYPES['ERROR']:
                    print(f"\n[ERROR] {msg.content}")
                
                print(f"{self.username}> ", end="", flush=True)
            
            except Exception as e:
                if self.running:
                    print(f"\n[ERROR] {e}")
                break
    
    def send_messages(self):
        """Hilo principal para enviar mensajes"""
        try:
            while self.running:
                try:
                    user_input = input(f"{self.username}> ").strip()
                except EOFError:
                    break
                
                if not user_input:
                    continue
                
                if user_input.startswith("/salir"):
                    msg = Message(MSG_TYPES['DISCONNECT'], self.username)
                    self.client_socket.send(msg)
                    print("[!] Desconectando...")
                    break
                
                elif user_input.startswith("/usuarios"):
                    msg = Message(MSG_TYPES['LIST_USERS'], self.username)
                    self.client_socket.send(msg)
                
                elif user_input.startswith("/msg "):
                    parts = user_input[5:].split(" ", 1)
                    if len(parts) < 2:
                        print("[!] Uso: /msg <usuario> <mensaje>")
                        continue
                    recipient, content = parts
                    msg = Message(MSG_TYPES['PRIVATE'], self.username, content, recipient)
                    self.client_socket.send(msg)
                
                elif user_input.startswith("/ayuda"):
                    self.display_help()
                
                elif user_input.startswith("/"):
                    print("[!] Comando no reconocido. Use /ayuda")
                
                else:
                    msg = Message(MSG_TYPES['BROADCAST'], self.username, user_input)
                    self.client_socket.send(msg)
        
        except Exception as e:
            print(f"[ERROR] {e}")
        finally:
            self.running = False
    
    def connect(self):
        """Conecta al servidor y registra el usuario"""
        try:
            self.client_socket.connect()
            
            # Solicitar nombre de usuario
            while True:
                self.username = input("Ingrese su nombre de usuario: ").strip()
                if self.username and len(self.username) <= 20:
                    if " " not in self.username:
                        break
                print("[!] Nombre inválido (sin espacios, máx 20 caracteres)")
            
            # Enviar registro
            msg = Message(MSG_TYPES['REGISTER'], self.username)
            self.client_socket.send(msg)
            
            # Iniciar hilo receptor
            recv_thread = threading.Thread(target=self.receive_messages)
            recv_thread.daemon = True
            recv_thread.start()
            
            # Esperar confirmación
            import time
            time.sleep(0.5)
            
            if self.running:
                self.send_messages()
        
        except ConnectionRefusedError:
            print("[ERROR] No se pudo conectar al servidor")
        except KeyboardInterrupt:
            print("\n[!] Interrumpido por el usuario")
        finally:
            self.running = False
            self.client_socket.close()
            print("[!] Conexión cerrada")


if __name__ == "__main__":
    client = ChatClient()
    client.connect()
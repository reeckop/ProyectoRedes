import socket
import threading
import sys
import json
import comun

# Estructura para guardar clientes: { "nombre_usuario": direccion_o_socket }
clientes = {}
lock = threading.Lock()

def log(texto):
    """Imprime y fuerza el flush para que se vea en la GUI"""
    print(texto)
    sys.stdout.flush()

def manejar_mensaje(datos, addr, sock_servidor, es_tcp):
    msg = comun.desempaquetar_mensaje(datos)
    if not msg: 
        return False

    tipo = msg['tipo']
    usuario = msg['usuario']
    
    with lock:
        # 1. REGISTRO
        if tipo == "REGISTRO":
            if usuario in clientes:
                error = comun.empaquetar_mensaje("ERROR", "SERVER", "Nombre en uso.")
                enviar_datos(sock_servidor, error, addr, es_tcp)
                return False
            
            # Guardamos el cliente
            clientes[usuario] = addr 
            log(f"[+] Nuevo usuario: {usuario} desde {addr}")
            
            # Mensaje de bienvenida/aviso
            broadcast(sock_servidor, "SERVER", f"{usuario} se ha unido.", es_tcp)
            return True

        # 2. MENSAJE PÚBLICO
        elif tipo == "PUBLICO":
            log(f"[Publico] {usuario}: {msg['contenido']}")
            retransmitir_a_todos(sock_servidor, msg, es_tcp)

        # 3. MENSAJE PRIVADO
        elif tipo == "PRIVADO":
            destino = msg['destino']
            if destino in clientes:
                log(f"[Privado] {usuario} -> {destino}")
                payload = comun.empaquetar_mensaje("PRIVADO", usuario, msg['contenido'])
                enviar_datos(sock_servidor, payload, clientes[destino], es_tcp)
            else:
                error = comun.empaquetar_mensaje("ERROR", "SERVER", f"Usuario {destino} no existe.")
                enviar_datos(sock_servidor, error, addr, es_tcp)
    
    return True

def enviar_datos(sock, datos, destino, es_tcp):
    try:
        if es_tcp:
            destino.send(datos)
        else:
            sock.sendto(datos, destino)
    except Exception as e:
        log(f"Error enviando datos: {e}")

def broadcast(sock, remitente, texto, es_tcp):
    msg = comun.empaquetar_mensaje("PUBLICO", remitente, texto)
    for nombre, destino in clientes.items():
        enviar_datos(sock, msg, destino, es_tcp)

def retransmitir_a_todos(sock, msg_dict, es_tcp):
    datos = json.dumps(msg_dict).encode('utf-8')
    for nombre, destino in clientes.items():
        enviar_datos(sock, datos, destino, es_tcp)

# --- LÓGICA ESPECÍFICA TCP ---
def cliente_thread_tcp(conn, addr):
    log(f"[Conexión TCP Entrante] {addr}")
    conectado = True
    usuario_actual = None
    
    while conectado:
        try:
            datos = conn.recv(comun.BUFSIZE)
            if not datos: break
            
            if usuario_actual is None:
                msg = comun.desempaquetar_mensaje(datos)
                if msg: usuario_actual = msg['usuario']

            conectado = manejar_mensaje(datos, conn, None, True)
        except Exception as e:
            log(f"Error TCP: {e}")
            break
            
    conn.close()
    with lock:
        if usuario_actual and usuario_actual in clientes:
            del clientes[usuario_actual]
            log(f"[-] Usuario desconectado: {usuario_actual}")

def iniciar_servidor():
    # Detectar Argumento desde GUI
    protocolo_str = "TCP"
    if len(sys.argv) > 1:
        protocolo_str = sys.argv[1].upper()
    
    if protocolo_str == "UDP":
        comun.PROTOCOLO = socket.SOCK_DGRAM
        es_tcp = False
        log(">>> INICIANDO EN MODO UDP <<<")
    else:
        comun.PROTOCOLO = socket.SOCK_STREAM
        es_tcp = True
        log(">>> INICIANDO EN MODO TCP <<<")
    
    servidor = socket.socket(socket.AF_INET, comun.PROTOCOLO)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        servidor.bind((comun.HOST, comun.PORT))
    except Exception as e:
        log(f"!!! Error FATAL al iniciar: {e}")
        return

    # Intentar obtener IP local real
    try:
        s_temp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s_temp.connect(("8.8.8.8", 80))
        ip_local = s_temp.getsockname()[0]
        s_temp.close()
    except:
        ip_local = "127.0.0.1"

    log(f"Escuchando en IP: {ip_local}")
    log(f"Puerto: {comun.PORT}")
    log(f"Esperando conexiones...")

    if es_tcp:
        servidor.listen()
        while True:
            conn, addr = servidor.accept()
            hilo = threading.Thread(target=cliente_thread_tcp, args=(conn, addr))
            hilo.start()
    else:
        while True:
            try:
                datos, addr = servidor.recvfrom(comun.BUFSIZE)
                manejar_mensaje(datos, addr, servidor, False)
            except Exception as e:
                log(f"Error en loop UDP: {e}")

if __name__ == "__main__":
    iniciar_servidor()
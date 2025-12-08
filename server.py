import socket
import threading
import comun

# Estructura para guardar clientes: { "nombre_usuario": direccion_o_socket }
clientes = {}
lock = threading.Lock()

def manejar_mensaje(datos, addr, sock_servidor, es_tcp):
    """Procesa el mensaje recibido (lógica común para TCP y UDP)."""
    msg = comun.desempaquetar_mensaje(datos)
    if not msg: return

    tipo = msg['tipo']
    usuario = msg['usuario']
    
    with lock:
        # 1. REGISTRO
        if tipo == "REGISTRO":
            if len(clientes) >= comun.MAX_CLIENTES:
                error = comun.empaquetar_mensaje("ERROR", "SERVER", "Sala llena.")
                enviar_datos(sock_servidor, error, addr, es_tcp)
                return False # Indica desconexión forzada si es TCP
            
            if usuario in clientes:
                error = comun.empaquetar_mensaje("ERROR", "SERVER", "Nombre en uso.")
                enviar_datos(sock_servidor, error, addr, es_tcp)
                return False
            
            # Guardamos el socket (TCP) o la dirección (UDP)
            clientes[usuario] = addr 
            print(f"[+] Nuevo usuario registrado: {usuario}")
            
            # Avisar a todos
            broadcast(sock_servidor, "SERVER", f"{usuario} se ha unido.", es_tcp)
            return True

        # 2. MENSAJE PÚBLICO
        elif tipo == "PUBLICO":
            print(f"[Publico] {usuario}: {msg['contenido']}")
            retransmitir_a_todos(sock_servidor, msg, es_tcp)

        # 3. MENSAJE PRIVADO
        elif tipo == "PRIVADO":
            destino = msg['destino']
            if destino in clientes:
                print(f"[Privado] {usuario} -> {destino}")
                payload = comun.empaquetar_mensaje("PRIVADO", usuario, msg['contenido'])
                enviar_datos(sock_servidor, payload, clientes[destino], es_tcp)
            else:
                error = comun.empaquetar_mensaje("ERROR", "SERVER", f"Usuario {destino} no encontrado.")
                enviar_datos(sock_servidor, error, addr, es_tcp)
    
    return True

def enviar_datos(sock, datos, destino, es_tcp):
    """Abstracción de envío."""
    try:
        if es_tcp:
            # En TCP, 'destino' es el objeto socket del cliente
            destino.send(datos)
        else:
            # En UDP, 'destino' es la tupla (ip, puerto)
            sock.sendto(datos, destino)
    except:
        pass

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
    print(f"[Conexión] {addr}")
    conectado = True
    usuario_actual = None
    
    while conectado:
        try:
            datos = conn.recv(comun.BUFSIZE)
            if not datos: break
            
            # Si es el primer mensaje, esperamos que sea registro y obtenemos el nombre
            if usuario_actual is None:
                msg = comun.desempaquetar_mensaje(datos)
                if msg: usuario_actual = msg['usuario']

            conectado = manejar_mensaje(datos, conn, None, True)
        except:
            break
            
    # Limpieza al desconectar
    conn.close()
    with lock:
        if usuario_actual and usuario_actual in clientes:
            del clientes[usuario_actual]
            print(f"[-] Usuario desconectado: {usuario_actual}")

def iniciar_servidor():
    es_tcp = (comun.PROTOCOLO == socket.SOCK_STREAM)
    servidor = socket.socket(socket.AF_INET, comun.PROTOCOLO)
    servidor.bind((comun.HOST, comun.PORT))

    print(f"--- SERVIDOR INICIADO ({'TCP' if es_tcp else 'UDP'}) ---")
    print(f"Escuchando en {comun.HOST}:{comun.PORT}")

    if es_tcp:
        servidor.listen()
        while True:
            conn, addr = servidor.accept()
            # En TCP, cada cliente tiene su propio hilo
            hilo = threading.Thread(target=cliente_thread_tcp, args=(conn, addr))
            hilo.start()
    else:
        # LÓGICA UDP (Todo en un solo hilo principal generalmente, o cola de mensajes)
        while True:
            datos, addr = servidor.recvfrom(comun.BUFSIZE)
            # En UDP, procesamos el paquete individualmente
            manejar_mensaje(datos, addr, servidor, False)

if __name__ == "__main__":
    iniciar_servidor()
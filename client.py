import socket
import threading
import sys
import comun

def recibir_mensajes(sock, es_tcp):
    while True:
        try:
            if es_tcp:
                datos = sock.recv(comun.BUFSIZE)
            else:
                datos, _ = sock.recvfrom(comun.BUFSIZE)
            
            if not datos: break
            
            msg = comun.desempaquetar_mensaje(datos)
            if msg:
                hora = msg['fecha'].split(' ')[1] # Solo hora
                if msg['tipo'] == "ERROR":
                    print(f"!!! Error: {msg['contenido']}")
                    if "llena" in msg['contenido'] or "en uso" in msg['contenido']:
                        sys.exit()
                elif msg['tipo'] == "PRIVADO":
                    print(f"[{hora}] (PRIVADO de {msg['usuario']}): {msg['contenido']}")
                else:
                    print(f"[{hora}] {msg['usuario']}: {msg['contenido']}")
        except OSError:
            break
        except Exception as e:
            print(f"Error recibiendo: {e}")
            break

def iniciar_cliente():
    nombre = input("Ingresa tu nombre de usuario: ")
    es_tcp = (comun.PROTOCOLO == socket.SOCK_STREAM)
    
    sock = socket.socket(socket.AF_INET, comun.PROTOCOLO)
    
    if es_tcp:
        try:
            sock.connect((comun.HOST, comun.PORT))
        except:
            print("No se pudo conectar al servidor.")
            return

    # 1. Enviar registro
    registro = comun.empaquetar_mensaje("REGISTRO", nombre, "Hola")
    if es_tcp:
        sock.send(registro)
    else:
        sock.sendto(registro, (comun.HOST, comun.PORT))

    # 2. Hilo para escuchar mensajes
    hilo = threading.Thread(target=recibir_mensajes, args=(sock, es_tcp))
    hilo.daemon = True
    hilo.start()

    print(f"--- Bienvenido al Chat {nombre} ---")
    print("Escribe tu mensaje y presiona Enter.")
    print("Para privado usa: /p usuario mensaje")
    print("Para salir: /salir")

    # 3. Bucle principal de envio
    while True:
        try:
            texto = input()
            if texto == "/salir":
                break
            
            tipo = "PUBLICO"
            destino = None
            contenido = texto

            # Detectar mensaje privado
            if texto.startswith("/p "):
                partes = texto.split(" ", 2)
                if len(partes) >= 3:
                    tipo = "PRIVADO"
                    destino = partes[1]
                    contenido = partes[2]
                else:
                    print("Formato incorrecto. Usa: /p usuario mensaje")
                    continue

            paquete = comun.empaquetar_mensaje(tipo, nombre, contenido, destino)
            
            if es_tcp:
                sock.send(paquete)
            else:
                sock.sendto(paquete, (comun.HOST, comun.PORT))
                
        except KeyboardInterrupt:
            break
            
    sock.close()

if __name__ == "__main__":
    iniciar_cliente()
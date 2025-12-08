"""
Cliente de consola para chat TCP/UDP
"""

import socket
import threading
import sys
import comun

def recibir_mensajes(sock, es_tcp, nombre, host, puerto):
    """
    Hilo para recibir mensajes del servidor.
    
    Args:
        sock: Socket conectado
        es_tcp: True para TCP, False para UDP
        nombre: Nombre del usuario
        host: Host del servidor (para UDP)
        puerto: Puerto del servidor (para UDP)
    """
    while True:
        try:
            if es_tcp:
                # TCP: recv bloqueante
                datos = sock.recv(comun.BUFSIZE)
                if not datos:
                    print("\n[!] Conexión cerrada por el servidor.")
                    break
            else:
                # UDP: recvfrom con timeout para salir del bucle
                sock.settimeout(1.0)  # Timeout de 1 segundo
                try:
                    datos, _ = sock.recvfrom(comun.BUFSIZE)
                except socket.timeout:
                    continue  # Timeout, volver a intentar
                except (ConnectionResetError, OSError):
                    print("\n[!] Error de conexión UDP.")
                    break
                finally:
                    sock.settimeout(None)  # Restaurar
            
            # Procesar mensaje recibido
            msg = comun.desempaquetar_mensaje(datos)
            if not msg:
                continue
            
            hora = msg.get('fecha', '').split(' ')[1] if 'fecha' in msg else '--:--'
            tipo = msg.get('tipo', '')
            usuario = msg.get('usuario', '')
            contenido = msg.get('contenido', '')
            
            # Manejar diferentes tipos de mensajes
            if tipo == "ERROR":
                print(f"\n[ERROR] {contenido}")
                # Errores críticos terminan la conexión
                if "llena" in contenido or "en uso" in contenido:
                    print("[!] Saliendo...")
                    sys.exit(1)
            
            elif tipo == "PRIVADO":
                if usuario == nombre:
                    # Mensaje privado enviado por mí
                    destino = msg.get('destino', 'alguien')
                    print(f"\n[{hora}] (Privado a {destino}): {contenido}")
                else:
                    # Mensaje privado recibido
                    print(f"\n[{hora}] (Privado de {usuario}): {contenido}")
            
            elif tipo == "SISTEMA":
                print(f"\n[SISTEMA] {contenido}")
            
            else:  # PUBLICO o cualquier otro
                print(f"\n[{hora}] {usuario}: {contenido}")
            
            # Mostrar prompt nuevamente
            sys.stdout.write("> ")
            sys.stdout.flush()
                
        except (ConnectionResetError, ConnectionAbortedError):
            print("\n[!] Conexión perdida con el servidor.")
            break
        except Exception as e:
            print(f"\n[ERROR] Error recibiendo mensaje: {e}")
            break

def conectar_al_servidor(host, puerto, es_tcp):
    """
    Establece conexión con el servidor.
    
    Returns:
        socket: Socket conectado o None si hay error
    """
    try:
        if es_tcp:
            sock = comun.crear_socket_tcp()
            sock.connect((host, puerto))
            print(f"[+] Conectado a {host}:{puerto} (TCP)")
            return sock
        else:
            sock = comun.crear_socket_udp()
            # UDP no tiene conexión real, solo guardamos el socket
            print(f"[+] Conectado a {host}:{puerto} (UDP)")
            return sock
            
    except ConnectionRefusedError:
        print(f"[ERROR] No se pudo conectar a {host}:{puerto}")
        print("       Asegúrate de que el servidor esté ejecutándose.")
        return None
    except Exception as e:
        print(f"[ERROR] No se pudo conectar: {e}")
        return None

def iniciar_cliente():
    """
    Función principal del cliente.
    Interfaz interactiva por consola.
    """
    print("=" * 40)
    print("        CHAT TCP/UDP - CLIENTE")
    print("=" * 40)
    
    # Configuración de conexión
    host = input("IP del servidor [127.0.0.1]: ").strip() or "127.0.0.1"
    
    try:
        puerto = int(input("Puerto [5000]: ").strip() or "5000")
    except ValueError:
        print("[ERROR] Puerto inválido. Usando puerto 5000.")
        puerto = 5000
    
    # Selección de protocolo
    while True:
        proto = input("Protocolo (TCP/UDP) [TCP]: ").strip().upper() or "TCP"
        if proto in ["TCP", "UDP"]:
            break
        print("[ERROR] Protocolo inválido. Usa TCP o UDP.")
    
    es_tcp = (proto == "TCP")
    
    # Nombre de usuario
    while True:
        nombre = input("Nombre de usuario: ").strip()
        if nombre:
            if len(nombre) > 20:
                print("[ERROR] El nombre no puede tener más de 20 caracteres.")
            else:
                break
        else:
            print("[ERROR] El nombre no puede estar vacío.")
    
    # Conectar al servidor
    sock = conectar_al_servidor(host, puerto, es_tcp)
    if not sock:
        return
    
    # Enviar registro al servidor
    registro = comun.empaquetar_mensaje("REGISTRO", nombre, "Conectándose...")
    try:
        if es_tcp:
            sock.send(registro)
        else:
            sock.sendto(registro, (host, puerto))
        print("[+] Registro enviado al servidor...")
    except Exception as e:
        print(f"[ERROR] Error al registrar usuario: {e}")
        sock.close()
        return
    
    # Iniciar hilo para recibir mensajes
    hilo_recibir = threading.Thread(target=recibir_mensajes, 
                                   args=(sock, es_tcp, nombre, host, puerto))
    hilo_recibir.daemon = True
    hilo_recibir.start()
    
    # Esperar breve momento para recibir confirmación
    import time
    time.sleep(0.5)
    
    # Mostrar información y comandos
    print("\n" + "=" * 40)
    print(f"Bienvenido, {nombre}!")
    print("=" * 40)
    print("\nComandos disponibles:")
    print("  /p usuario mensaje  - Enviar mensaje privado")
    print("  /salir              - Salir del chat")
    print("  /ayuda              - Mostrar esta ayuda")
    print("  /usuarios           - Listar usuarios conectados")
    print("  texto normal        - Mensaje público a todos")
    print("-" * 40)
    print("\nEscribe tu primer mensaje:")
    
    # Bucle principal para enviar mensajes
    try:
        while True:
            try:
                # Mostrar prompt
                sys.stdout.write("> ")
                sys.stdout.flush()
                
                # Leer entrada
                texto = input().strip()
                
                if not texto:
                    continue
                
                # Comandos especiales
                if texto.lower() == "/salir":
                    print("[+] Saliendo del chat...")
                    break
                
                if texto.lower() == "/ayuda":
                    print("\nComandos disponibles:")
                    print("  /p usuario mensaje  - Mensaje privado")
                    print("  /salir              - Salir")
                    print("  /ayuda              - Mostrar ayuda")
                    print("  /usuarios           - Listar usuarios")
                    print("  texto normal        - Mensaje público")
                    continue
                
                if texto.lower() == "/usuarios":
                    print("\n[INFO] Para ver usuarios conectados, espera mensajes del servidor.")
                    continue
                
                # Determinar tipo de mensaje
                tipo = "PUBLICO"
                destino = None
                contenido = texto
                
                if texto.startswith("/p "):
                    partes = texto.split(" ", 2)
                    if len(partes) >= 3:
                        tipo = "PRIVADO"
                        destino = partes[1]
                        contenido = partes[2]
                        print(f"[+] Enviando mensaje privado a {destino}...")
                    else:
                        print("[ERROR] Formato incorrecto. Usa: /p usuario mensaje")
                        continue
                else:
                    # Mensaje público - mostrar inmediatamente en consola
                    hora_actual = time.strftime("%H:%M")
                    print(f"[{hora_actual}] {nombre}: {contenido}")
                
                # Empacar y enviar mensaje
                paquete = comun.empaquetar_mensaje(tipo, nombre, contenido, destino)
                
                try:
                    if es_tcp:
                        sock.send(paquete)
                    else:
                        sock.sendto(paquete, (host, puerto))
                except Exception as e:
                    print(f"[ERROR] Error al enviar mensaje: {e}")
                    
            except KeyboardInterrupt:
                print("\n[!] Interrupción recibida. Saliendo...")
                break
            except EOFError:
                print("\n[!] Fin de entrada. Saliendo...")
                break
            except Exception as e:
                print(f"[ERROR] Error: {e}")
    
    finally:
        # Cerrar conexión
        try:
            sock.close()
        except:
            pass
        print("[+] Conexión cerrada. ¡Hasta pronto!")

if __name__ == "__main__":
    iniciar_cliente()
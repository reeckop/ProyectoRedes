# Proyecto Final - Chat TCP/UDP

## Descripción
Sistema de chat en tiempo real con soporte para protocolos TCP y UDP, desarrollado en Python para la materia de Redes 2025.

## Características
- Soporte dual para protocolos TCP y UDP
- Interfaz gráfica moderna (GUI) y línea de comandos (CLI)
- Mensajes públicos y privados
- Registro de usuarios con nombres únicos
- Límite de 5 clientes simultáneos
- Timestamp en todos los mensajes
- Arquitectura cliente-servidor
- Multi-hilos para manejo concurrente

## Estructura del Proyecto
─ comun.py      # Módulo compartido (serialización/configuración)
─ servidor.py   # Servidor TCP/UDP
─ client.py     # Cliente de consola
─ guicliente.py # Cliente con interfaz gráfica
─ gui.py        # Gestor principal (inicia servidor/clientes)
─ README.md     # Esta documentación

## Instalación y Ejecución

### Requisitos
- Python 3.6 o superior
- No se requieren librerías externas (usa bibliotecas estándar)

### Método 1: Gestor Principal (Recomendado)
- python gui.py
* Selecciona protocolo (TCP/UDP)
* Haz clic en "INICIAR SERVIDOR"
* Usa "ABRIR CLIENTE GUI" para probar


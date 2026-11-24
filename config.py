# ===================== CONFIGURACIÓN DEL FILTRO DE SEGURIDAD =====================
# Pines en numeración FÍSICA (BOARD), la misma que usa la librería mfrc522 por defecto.

PIN_LED_ROJO = 11     # GPIO17
PIN_LED_VERDE = 13    # GPIO27
PIN_SERVO = 12        # GPIO18 (PWM)

# Ángulos del servo (ajústalos a tu cerradura/puerta)
SERVO_CERRADO = 0
SERVO_ABIERTO = 90
TIEMPO_ABIERTO = 5    # segundos que la puerta queda abierta

# Usuarios autorizados.
#   clave del diccionario = UID de la tarjeta (sácalo con leer_tarjeta.py)
#   id_rostro = número con el que registraste la cara en registrar_rostro.py
#   contrasena = palabra que hay que decir en voz alta (sin acentos, minúsculas)
USUARIOS = {
    123456789012: {"nombre": "David", "id_rostro": 1, "contrasena": "dragon azul"},
    # 987654321098: {"nombre": "Ana", "id_rostro": 2, "contrasena": "sol de invierno"},
}

# Reconocimiento facial (LBPH: entre MÁS BAJO el valor, más parecido es)
UMBRAL_CONFIANZA = 70      # si te rechaza siendo tú, súbelo a 80; si acepta a otros, bájalo
COINCIDENCIAS_NECESARIAS = 3   # cuántos frames seguidos deben reconocerte
TIEMPO_MAX_CARA = 8        # segundos para reconocer la cara

# Archivos
CARPETA_ROSTROS = "rostros"
ARCHIVO_MODELO = "modelo_rostros.yml"

# Voz
IDIOMA_RECONOCIMIENTO = "es-MX"
VOZ_ESPEAK = "es-419"      # español latino en espeak-ng
INTENTOS_CONTRASENA = 2

# Resolución baja para no saturar 1 GB de RAM
ANCHO_CAMARA = 320
ALTO_CAMARA = 240

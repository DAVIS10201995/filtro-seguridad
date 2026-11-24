"""Pasa una tarjeta por el lector y muestra su UID para copiarlo en config.py."""
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
lector = SimpleMFRC522()

try:
    print("Acerca una tarjeta al lector... (Ctrl+C para salir)")
    while True:
        uid = lector.read_id()
        print(f"UID detectado: {uid}")
        input("Enter para leer otra...")
except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()

"""
FILTRO DE SEGURIDAD - 3 factores
  1) Tarjeta NFC/RFID (RC522)
  2) Reconocimiento facial (cámara + OpenCV LBPH)
  3) Contraseña por voz (micrófono + SpeechRecognition)
Actuadores: LED rojo, LED verde, bocina (espeak-ng) y servomotor.
"""
import subprocess
import time
import unicodedata

import cv2
import RPi.GPIO as GPIO
import speech_recognition as sr
from mfrc522 import SimpleMFRC522

import config
from camara import Camara, ruta_haarcascade

# ------------------------------------------------------------------ GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)          # antes de crear el lector RC522
GPIO.setup(config.PIN_LED_ROJO, GPIO.OUT)
GPIO.setup(config.PIN_LED_VERDE, GPIO.OUT)
GPIO.setup(config.PIN_SERVO, GPIO.OUT)
servo = GPIO.PWM(config.PIN_SERVO, 50)   # 50 Hz para servos
servo.start(0)
lector = SimpleMFRC522()


# ------------------------------------------------------------------ ACTUADORES
def led_rojo():
    GPIO.output(config.PIN_LED_VERDE, GPIO.LOW)
    GPIO.output(config.PIN_LED_ROJO, GPIO.HIGH)


def led_verde():
    GPIO.output(config.PIN_LED_ROJO, GPIO.LOW)
    GPIO.output(config.PIN_LED_VERDE, GPIO.HIGH)


def parpadear_rojo(veces=3):
    for _ in range(veces):
        GPIO.output(config.PIN_LED_ROJO, GPIO.LOW)
        time.sleep(0.2)
        GPIO.output(config.PIN_LED_ROJO, GPIO.HIGH)
        time.sleep(0.2)


def mover_servo(angulo):
    servo.ChangeDutyCycle(2.5 + angulo / 18.0)   # 0° = 2.5 %, 180° = 12.5 %
    time.sleep(0.6)
    servo.ChangeDutyCycle(0)                     # evita que tiemble


def decir(texto):
    print(f"[BOCINA] {texto}")
    subprocess.run(["espeak-ng", "-v", config.VOZ_ESPEAK, "-s", "150", texto],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ------------------------------------------------------------------ SENSORES
def esperar_tarjeta():
    print("\nEsperando tarjeta...")
    uid = lector.read_id()          # bloquea hasta que pasen una tarjeta
    print(f"[NFC] UID: {uid}")
    return uid


def reconocer_cara(id_esperado):
    """True si la cámara reconoce al dueño de la tarjeta."""
    modelo = cv2.face.LBPHFaceRecognizer_create()
    modelo.read(config.ARCHIVO_MODELO)
    detector = cv2.CascadeClassifier(ruta_haarcascade())
    cam = Camara()
    aciertos = 0
    inicio = time.time()
    try:
        while time.time() - inicio < config.TIEMPO_MAX_CARA:
            gris = cam.leer_gris()
            if gris is None:
                continue
            caras = detector.detectMultiScale(gris, 1.2, 5, minSize=(60, 60))
            for (x, y, w, h) in caras[:1]:
                rostro = cv2.resize(gris[y:y + h, x:x + w], (150, 150))
                etiqueta, confianza = modelo.predict(rostro)
                print(f"[CÁMARA] id={etiqueta} confianza={confianza:.1f}")
                if etiqueta == id_esperado and confianza < config.UMBRAL_CONFIANZA:
                    aciertos += 1
                    if aciertos >= config.COINCIDENCIAS_NECESARIAS:
                        return True
                else:
                    aciertos = 0
        return False
    finally:
        cam.cerrar()                # libera la cámara y RAM


def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn").strip()


def escuchar_contrasena(contrasena):
    rec = sr.Recognizer()
    with sr.Microphone() as fuente:
        rec.adjust_for_ambient_noise(fuente, duration=0.5)
        for intento in range(1, config.INTENTOS_CONTRASENA + 1):
            decir("Diga la contraseña")
            try:
                audio = rec.listen(fuente, timeout=5, phrase_time_limit=4)
                texto = normalizar(rec.recognize_google(audio, language=config.IDIOMA_RECONOCIMIENTO))
                print(f"[MICRÓFONO] Escuché: '{texto}'")
                if normalizar(contrasena) in texto:
                    return True
            except sr.WaitTimeoutError:
                print("[MICRÓFONO] No se escuchó nada")
            except sr.UnknownValueError:
                print("[MICRÓFONO] No se entendió")
            except sr.RequestError as e:
                print(f"[MICRÓFONO] Error del servicio de voz: {e}")
            if intento < config.INTENTOS_CONTRASENA:
                decir("Contraseña incorrecta, intente de nuevo")
    return False


# ------------------------------------------------------------------ RESULTADOS
def acceso_permitido(nombre):
    led_verde()
    decir(f"Acceso permitido. Bienvenido {nombre}")
    mover_servo(config.SERVO_ABIERTO)
    time.sleep(config.TIEMPO_ABIERTO)
    mover_servo(config.SERVO_CERRADO)
    led_rojo()


def acceso_denegado(motivo):
    print(f"[DENEGADO] {motivo}")
    parpadear_rojo()
    decir("Acceso denegado")


# ------------------------------------------------------------------ PROGRAMA PRINCIPAL
def main():
    led_rojo()
    mover_servo(config.SERVO_CERRADO)
    decir("Sistema de seguridad listo")
    while True:
        # Paso 1: tarjeta
        uid = esperar_tarjeta()
        usuario = config.USUARIOS.get(uid)
        if not usuario:
            acceso_denegado("Tarjeta no registrada")
            time.sleep(1)
            continue

        # Paso 2: cara
        decir(f"Hola {usuario['nombre']}, mire a la cámara")
        if not reconocer_cara(usuario["id_rostro"]):
            acceso_denegado("Rostro no reconocido")
            time.sleep(1)
            continue
        decir("Rostro verificado")

        # Paso 3: contraseña por voz
        if not escuchar_contrasena(usuario["contrasena"]):
            acceso_denegado("Contraseña incorrecta")
            time.sleep(1)
            continue

        acceso_permitido(usuario["nombre"])
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSaliendo...")
    finally:
        servo.stop()
        GPIO.cleanup()

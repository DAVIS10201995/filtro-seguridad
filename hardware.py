"""
Capa de hardware.
  HardwareReal     -> Raspberry con RC522, cámara, micrófono, LEDs, servo y bocina.
  HardwareSimulado -> sin nada conectado; las tarjetas se "pasan" desde la página web.
"""
import os
import queue
import subprocess
import time
import unicodedata

import config


def modo_simulacion():
    valor = os.environ.get("SIMULAR")
    if valor is not None:
        return valor == "1"
    return config.MODO_SIMULACION


def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn").strip()


def _espeak(texto):
    try:
        subprocess.run(["espeak-ng", "-v", config.VOZ_ESPEAK, "-s", "150", texto],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        pass   # sin espeak-ng (por ejemplo en Windows) solo se imprime


# =============================================================== REAL
class HardwareReal:
    simulado = False

    def __init__(self):
        import RPi.GPIO as GPIO
        from mfrc522 import SimpleMFRC522
        self.GPIO = GPIO
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)          # antes de crear el lector RC522
        for pin in (config.PIN_LED_ROJO, config.PIN_LED_VERDE, config.PIN_SERVO):
            GPIO.setup(pin, GPIO.OUT)
        self.pwm = GPIO.PWM(config.PIN_SERVO, 50)
        self.pwm.start(0)
        self.lector = SimpleMFRC522()

    def led(self, color):
        G = self.GPIO
        G.output(config.PIN_LED_ROJO, G.HIGH if color == "rojo" else G.LOW)
        G.output(config.PIN_LED_VERDE, G.HIGH if color == "verde" else G.LOW)

    def servo(self, angulo):
        self.pwm.ChangeDutyCycle(2.5 + angulo / 18.0)
        time.sleep(0.6)
        self.pwm.ChangeDutyCycle(0)       # evita que tiemble

    def decir(self, texto):
        print(f"[BOCINA] {texto}")
        _espeak(texto)

    def leer_tarjeta(self, timeout=1.0):
        """Devuelve el UID o None si no pasó ninguna tarjeta en 'timeout' segundos."""
        fin = time.time() + timeout
        while time.time() < fin:
            uid = self.lector.read_id_no_block()
            if uid:
                return uid
            time.sleep(0.1)
        return None

    def reconocer_cara(self, id_esperado):
        import cv2
        from camara import Camara, ruta_haarcascade
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
            cam.cerrar()

    def escuchar_contrasena(self, contrasena, decir):
        import speech_recognition as sr
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

    def cerrar(self):
        self.pwm.stop()
        self.GPIO.cleanup()


# =============================================================== SIMULADO
class HardwareSimulado:
    simulado = True

    def __init__(self):
        self.cola = queue.Queue()
        self.cara_ok = True
        self.voz_ok = True
        print("*** MODO SIMULACIÓN: sin sensores ni actuadores ***")

    def led(self, color):
        print(f"[SIM LED] {color}")

    def servo(self, angulo):
        print(f"[SIM SERVO] {angulo}°")
        time.sleep(0.6)

    def decir(self, texto):
        print(f"[SIM BOCINA] {texto}")
        _espeak(texto)

    def simular_tarjeta(self, uid, cara_ok, voz_ok):
        self.cola.put((uid, cara_ok, voz_ok))

    def leer_tarjeta(self, timeout=1.0):
        try:
            uid, self.cara_ok, self.voz_ok = self.cola.get(timeout=timeout)
            return uid
        except queue.Empty:
            return None

    def reconocer_cara(self, id_esperado):
        time.sleep(1.5)
        return self.cara_ok

    def escuchar_contrasena(self, contrasena, decir):
        decir("Diga la contraseña")
        time.sleep(1.5)
        return self.voz_ok

    def cerrar(self):
        pass


def crear_hardware():
    return HardwareSimulado() if modo_simulacion() else HardwareReal()

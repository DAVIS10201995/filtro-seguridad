"""
FILTRO DE SEGURIDAD - 3 factores
  1) Tarjeta NFC/RFID (RC522)
  2) Reconocimiento facial (cámara + OpenCV LBPH)
  3) Contraseña por voz (micrófono + SpeechRecognition)
Actuadores: LED rojo, LED verde, bocina (espeak-ng) y servomotor.

Se puede correr solo (python control_acceso.py) o junto con la página web (python app.py).
"""
import threading
import time
from collections import deque
from datetime import datetime

import config
from hardware import crear_hardware


class SistemaAcceso:
    def __init__(self):
        self.hw = crear_hardware()
        self.lock_actuadores = threading.Lock()   # servo/LEDs: una acción a la vez
        self.lock_voz = threading.Lock()          # que no hablen dos cosas al mismo tiempo
        self.activo = True        # False = pausado desde la web (no lee tarjetas)
        self.corriendo = True
        self.puerta = "cerrada"
        self.led_actual = "rojo"
        self.paso = "Iniciando"
        self._cerrar_ahora = False
        self.registros = deque(maxlen=30)
        self._led("rojo")
        self.hw.servo(config.SERVO_CERRADO)

    # ---------------------------------------------------------- utilidades
    def _led(self, color):
        self.hw.led(color)
        self.led_actual = color

    def decir(self, texto):
        with self.lock_voz:
            self.hw.decir(texto)

    def registrar(self, evento, resultado, usuario="-"):
        self.registros.appendleft({
            "hora": datetime.now().strftime("%H:%M:%S"),
            "usuario": usuario,
            "evento": evento,
            "resultado": resultado,
        })
        print(f"[REGISTRO] {usuario} | {evento} | {resultado}")

    def estado(self):
        datos = {
            "simulacion": self.hw.simulado,
            "activo": self.activo,
            "puerta": self.puerta,
            "led": self.led_actual,
            "paso": self.paso,
            "registros": list(self.registros),
        }
        if self.hw.simulado:
            datos["usuarios"] = [{"uid": uid, "nombre": u["nombre"]} for uid, u in config.USUARIOS.items()]
        return datos

    # ---------------------------------------------------------- actuadores
    def abrir_puerta(self, mensaje=None):
        """LED verde, mensaje, abre el servo, espera y cierra. False si ya estaba ocupada."""
        if not self.lock_actuadores.acquire(blocking=False):
            return False
        try:
            self._cerrar_ahora = False
            self._led("verde")
            if mensaje:
                self.decir(mensaje)
            self.puerta = "abierta"
            self.hw.servo(config.SERVO_ABIERTO)
            fin = time.time() + config.TIEMPO_ABIERTO
            while time.time() < fin and not self._cerrar_ahora:
                time.sleep(0.1)
            self.hw.servo(config.SERVO_CERRADO)
            self.puerta = "cerrada"
            self._led("rojo")
        finally:
            self.lock_actuadores.release()
        return True

    def cerrar_puerta(self):
        self._cerrar_ahora = True

    def denegar(self, motivo, usuario="-"):
        self.registrar(motivo, "DENEGADO", usuario)
        with self.lock_actuadores:
            for _ in range(3):
                self._led("apagado")
                time.sleep(0.2)
                self._led("rojo")
                time.sleep(0.2)
        self.decir("Acceso denegado")

    # ---------------------------------------------------------- flujo de acceso
    def verificar(self, uid):
        usuario = config.USUARIOS.get(uid)
        if not usuario:
            self.denegar(f"Tarjeta no registrada ({uid})")
            return
        nombre = usuario["nombre"]

        self.paso = f"Verificando rostro de {nombre}"
        self.decir(f"Hola {nombre}, mire a la cámara")
        if not self.hw.reconocer_cara(usuario["id_rostro"]):
            self.denegar("Rostro no reconocido", nombre)
            return
        self.decir("Rostro verificado")

        self.paso = f"Esperando contraseña de {nombre}"
        if not self.hw.escuchar_contrasena(usuario["contrasena"], self.decir):
            self.denegar("Contraseña incorrecta", nombre)
            return

        self.registrar("Tarjeta + rostro + contraseña", "PERMITIDO", nombre)
        self.paso = f"Puerta abierta para {nombre}"
        self.abrir_puerta(f"Acceso permitido. Bienvenido {nombre}")

    def bucle(self):
        self.decir("Sistema de seguridad listo")
        while self.corriendo:
            if not self.activo:
                self.paso = "Sistema pausado"
                time.sleep(0.5)
                continue
            if self.puerta == "abierta":
                time.sleep(0.2)
                continue
            self.paso = "Esperando tarjeta"
            uid = self.hw.leer_tarjeta(timeout=1)
            if uid is None:
                continue
            print(f"[NFC] UID: {uid}")
            self.verificar(uid)
            time.sleep(1)


if __name__ == "__main__":
    sistema = SistemaAcceso()
    try:
        sistema.bucle()
    except KeyboardInterrupt:
        print("\nSaliendo...")
    finally:
        sistema.hw.cerrar()

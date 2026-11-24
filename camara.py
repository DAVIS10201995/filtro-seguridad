"""Utilidades de cámara compartidas: funciona con la cámara oficial (picamera2) o una webcam USB."""
import os
import cv2
import config


def ruta_haarcascade():
    nombre = "haarcascade_frontalface_default.xml"
    candidatos = []
    if hasattr(cv2, "data"):
        candidatos.append(os.path.join(cv2.data.haarcascades, nombre))
    candidatos += [
        f"/usr/share/opencv4/haarcascades/{nombre}",
        f"/usr/share/opencv/haarcascades/{nombre}",
        nombre,
    ]
    for ruta in candidatos:
        if os.path.exists(ruta):
            return ruta
    raise FileNotFoundError("No encontré haarcascade_frontalface_default.xml")


class Camara:
    def __init__(self):
        self.picam = None
        self.cap = None
        try:
            from picamera2 import Picamera2
            self.picam = Picamera2()
            cfg = self.picam.create_preview_configuration(
                main={"size": (config.ANCHO_CAMARA, config.ALTO_CAMARA), "format": "RGB888"}
            )
            self.picam.configure(cfg)
            self.picam.start()
        except Exception:
            self.picam = None
            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.ANCHO_CAMARA)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.ALTO_CAMARA)
            if not self.cap.isOpened():
                raise RuntimeError("No se pudo abrir ninguna cámara")

    def leer_gris(self):
        """Devuelve un frame en escala de grises (o None)."""
        if self.picam:
            frame = self.picam.capture_array()
            return cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        ok, frame = self.cap.read()
        if not ok:
            return None
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    def cerrar(self):
        if self.picam:
            self.picam.stop()
            self.picam.close()
        if self.cap:
            self.cap.release()

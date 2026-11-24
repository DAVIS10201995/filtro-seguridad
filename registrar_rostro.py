"""
Registra la cara de un usuario y entrena el modelo.
Uso:  python registrar_rostro.py 1      (1 = id_rostro que pondrás en config.py)
Al terminar con todos los usuarios, el modelo queda en modelo_rostros.yml
"""
import os
import sys
import time
import cv2
import numpy as np
import config
from camara import Camara, ruta_haarcascade

MUESTRAS = 40


def capturar(id_rostro):
    carpeta = os.path.join(config.CARPETA_ROSTROS, str(id_rostro))
    os.makedirs(carpeta, exist_ok=True)
    detector = cv2.CascadeClassifier(ruta_haarcascade())
    cam = Camara()
    print("Mira a la cámara. Mueve un poco la cabeza (izq, der, arriba, abajo)...")
    time.sleep(2)
    n = 0
    try:
        while n < MUESTRAS:
            gris = cam.leer_gris()
            if gris is None:
                continue
            caras = detector.detectMultiScale(gris, 1.2, 5, minSize=(60, 60))
            for (x, y, w, h) in caras[:1]:
                rostro = cv2.resize(gris[y:y + h, x:x + w], (150, 150))
                cv2.imwrite(os.path.join(carpeta, f"{n}.png"), rostro)
                n += 1
                print(f"  muestra {n}/{MUESTRAS}")
                time.sleep(0.15)
    finally:
        cam.cerrar()


def entrenar():
    imagenes, etiquetas = [], []
    for nombre in os.listdir(config.CARPETA_ROSTROS):
        carpeta = os.path.join(config.CARPETA_ROSTROS, nombre)
        if not nombre.isdigit() or not os.path.isdir(carpeta):
            continue
        for archivo in os.listdir(carpeta):
            img = cv2.imread(os.path.join(carpeta, archivo), cv2.IMREAD_GRAYSCALE)
            if img is not None:
                imagenes.append(img)
                etiquetas.append(int(nombre))
    if not imagenes:
        print("No hay imágenes para entrenar")
        return
    modelo = cv2.face.LBPHFaceRecognizer_create()
    modelo.train(imagenes, np.array(etiquetas))
    modelo.write(config.ARCHIVO_MODELO)
    print(f"Modelo entrenado con {len(imagenes)} imágenes -> {config.ARCHIVO_MODELO}")


if __name__ == "__main__":
    if len(sys.argv) < 2 or not sys.argv[1].isdigit():
        print("Uso: python registrar_rostro.py <id_rostro>")
        sys.exit(1)
    capturar(int(sys.argv[1]))
    entrenar()

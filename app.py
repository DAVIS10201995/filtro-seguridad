"""
Página web de control del filtro de seguridad.
Ejecuta:  python app.py      y abre  http://IP_DE_LA_PI:5000
"""
import os
import threading
from functools import wraps

from flask import Flask, Response, jsonify, request, send_from_directory

import config
from control_acceso import SistemaAcceso

CARPETA_WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
app = Flask(__name__, static_folder=None)
sistema = SistemaAcceso()


def requiere_login(f):
    @wraps(f)
    def envoltura(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != config.WEB_USUARIO or auth.password != config.WEB_PASSWORD:
            return Response("Acceso restringido", 401,
                            {"WWW-Authenticate": 'Basic realm="Filtro de seguridad"'})
        return f(*args, **kwargs)
    return envoltura


def en_segundo_plano(funcion, *args):
    threading.Thread(target=funcion, args=args, daemon=True).start()


@app.get("/")
@requiere_login
def inicio():
    return send_from_directory(CARPETA_WEB, "index.html")


@app.get("/api/estado")
@requiere_login
def estado():
    return jsonify(sistema.estado())


@app.post("/api/abrir")
@requiere_login
def abrir():
    if sistema.puerta == "abierta" or sistema.lock_actuadores.locked():
        return jsonify(ok=False, mensaje="La puerta está ocupada"), 409
    sistema.registrar("Apertura remota desde la web", "PERMITIDO", config.WEB_USUARIO)
    en_segundo_plano(sistema.abrir_puerta, "Apertura remota")
    return jsonify(ok=True)


@app.post("/api/cerrar")
@requiere_login
def cerrar():
    sistema.cerrar_puerta()
    sistema.registrar("Cierre remoto desde la web", "OK", config.WEB_USUARIO)
    return jsonify(ok=True)


@app.post("/api/sistema")
@requiere_login
def pausar_reanudar():
    datos = request.get_json(silent=True) or {}
    sistema.activo = bool(datos.get("activo", True))
    sistema.registrar("Sistema reanudado" if sistema.activo else "Sistema pausado", "OK", config.WEB_USUARIO)
    return jsonify(ok=True, activo=sistema.activo)


@app.post("/api/decir")
@requiere_login
def decir():
    texto = ((request.get_json(silent=True) or {}).get("texto") or "").strip()[:150]
    if not texto:
        return jsonify(ok=False, mensaje="Escribe un mensaje"), 400
    en_segundo_plano(sistema.decir, texto)
    return jsonify(ok=True)


@app.post("/api/simular_tarjeta")
@requiere_login
def simular_tarjeta():
    if not sistema.hw.simulado:
        return jsonify(ok=False, mensaje="Solo disponible en modo simulación"), 400
    datos = request.get_json(silent=True) or {}
    try:
        uid = int(datos.get("uid"))
    except (TypeError, ValueError):
        return jsonify(ok=False, mensaje="UID inválido"), 400
    sistema.hw.simular_tarjeta(uid, bool(datos.get("cara_ok")), bool(datos.get("voz_ok")))
    return jsonify(ok=True)


if __name__ == "__main__":
    threading.Thread(target=sistema.bucle, daemon=True).start()
    try:
        app.run(host="0.0.0.0", port=config.WEB_PUERTO, threaded=True)
    finally:
        sistema.corriendo = False
        sistema.hw.cerrar()

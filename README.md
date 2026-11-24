# Filtro de seguridad - Raspberry Pi (tarjeta + cara + voz)

## Conexiones (numeración física)

| Componente | Pin del componente | Pin Raspberry |
|---|---|---|
| RC522 | SDA | 24 (GPIO8 / CE0) |
| RC522 | SCK | 23 (GPIO11) |
| RC522 | MOSI | 19 (GPIO10) |
| RC522 | MISO | 21 (GPIO9) |
| RC522 | RST | 22 (GPIO25) |
| RC522 | 3.3V | 1 (**3.3 V, NO 5 V**) |
| RC522 | GND | 6 |
| LED rojo (+ resistencia 220 Ω) | ánodo | 11 (GPIO17) |
| LED verde (+ resistencia 220 Ω) | ánodo | 13 (GPIO27) |
| LEDs | cátodo | GND |
| Servo | señal (naranja/amarillo) | 12 (GPIO18) |
| Servo | VCC (rojo) | 5 V (mejor fuente externa) |
| Servo | GND (café) | GND (común con la Pi) |
| Cámara | — | puerto CSI o USB |
| Micrófono | — | USB |
| Bocina | — | jack 3.5 mm / USB / Bluetooth |

## Instalación

```bash
sudo raspi-config        # Interface Options -> SPI -> Enable (y reinicia)
sudo apt update
sudo apt install -y espeak-ng portaudio19-dev python3-picamera2 flac

source ~/venv-voz/bin/activate
pip install mfrc522 RPi.GPIO spidev SpeechRecognition pyaudio opencv-contrib-python-headless numpy
```

> Si usas la cámara oficial (CSI) dentro del venv, créalo con acceso a paquetes del sistema:
> `python3 -m venv --system-site-packages ~/venv-voz` (para que vea `picamera2`).

## Uso

1. `python leer_tarjeta.py` → copia el UID en `USUARIOS` de `config.py`.
2. `python registrar_rostro.py 1` → registra tu cara con id 1 (repite con 2, 3... para otros).
3. Pon la contraseña en `config.py` (minúsculas, sin acentos).
4. `python control_acceso.py`

## Flujo

Tarjeta → ¿registrada? → cara → ¿coincide con el dueño de la tarjeta? → contraseña por voz →
LED verde + "Acceso permitido" + servo abre 5 s → cierra y vuelve a rojo.
Si falla cualquier paso: LED rojo parpadea + "Acceso denegado".

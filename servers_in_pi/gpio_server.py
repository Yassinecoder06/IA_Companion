import asyncio
import json
import RPi.GPIO as GPIO
import smbus
import time
import websockets
from websockets.datastructures import Headers
from websockets.http11 import Response

PORT = 6000
WS_PUSH_INTERVAL = 0.1

# ---------------- GPIO ----------------
BUTTON_PINS = [4, 17, 27]
LIGHT_PINS = [23, 18, 24]

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

for pin in BUTTON_PINS:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

for pin in LIGHT_PINS:
    GPIO.setup(pin, GPIO.IN)

# ---------------- MPU6050 ----------------
bus = smbus.SMBus(1)
MPU_ADDR = 0x68
bus.write_byte_data(MPU_ADDR, 0x6B, 0)

# ---------------- STATE ----------------
gyro_enabled = False
gyro_bias = 0

faces = ["front", "right", "back", "left"]
face_index = 0

last_trigger = 0
TRIGGER_COOLDOWN = 0.6
VELOCITY_THRESHOLD = 100


# ---------------- READ SENSOR ----------------
def read_word(reg):
    high = bus.read_byte_data(MPU_ADDR, reg)
    low = bus.read_byte_data(MPU_ADDR, reg + 1)

    value = (high << 8) + low
    if value >= 0x8000:
        value = -((65535 - value) + 1)

    return value


def read_gyro():
    gx = read_word(0x43)
    gy = read_word(0x45)
    gz = read_word(0x47)
    return gx, gy, gz


# ---------------- CALIBRATION ----------------
def calibrate_gyro(samples=300):

    print("Calibrating gyro... keep device STILL")

    total = 0

    for _ in range(samples):
        gx, _, _ = read_gyro()
        total += gx
        time.sleep(0.005)

    bias = total / samples

    print("Gyro bias:", bias)

    return bias


# ---------------- FACE UPDATE ----------------
def update_face():

    global face_index, last_trigger

    gx, _, _ = read_gyro()

    raw_velocity = gx / 131.0

    now = time.time()

    if now - last_trigger < TRIGGER_COOLDOWN:
        return raw_velocity

    if raw_velocity > VELOCITY_THRESHOLD:
        face_index = (face_index + 1) % len(faces)
        last_trigger = now

    elif raw_velocity < -VELOCITY_THRESHOLD:
        face_index = (face_index - 1) % len(faces)
        last_trigger = now

    return raw_velocity


def get_orientation():
    return faces[face_index]


# ---------------- SERVER ----------------
def build_gpio_data():

    global gyro_enabled

    button_states = {pin: GPIO.input(pin) for pin in BUTTON_PINS}
    light_states = {pin: GPIO.input(pin) for pin in LIGHT_PINS}

    if not gyro_enabled:
        if all(GPIO.input(pin) == 0 for pin in BUTTON_PINS):
            print("Gyro activated")
            gyro_enabled = True

    gyro_state = None
    raw_velocity = None

    if gyro_enabled:
        raw_velocity = update_face()
        gyro_state = get_orientation()

    return {
        "buttons": button_states,
        "lights": light_states,
        "gyro_enabled": gyro_enabled,
        "gyro_orientation": gyro_state,
        "raw_velocity": raw_velocity
    }


async def ws_handler(websocket):
    try:
        while True:
            data = build_gpio_data()
            await websocket.send(json.dumps(data))
            await asyncio.sleep(WS_PUSH_INTERVAL)
    except websockets.exceptions.ConnectionClosed:
        pass


def process_request(connection, request):
    upgrade = request.headers.get("Upgrade", "").lower()

    if "websocket" in upgrade:
        return None

    if request.path == "/gpio":
        body = json.dumps(build_gpio_data()).encode()
        headers = Headers()
        headers["Content-Type"] = "application/json"
        headers["Content-Length"] = str(len(body))
        headers["Connection"] = "close"
        return Response(200, "OK", headers, body)

    body = b"WebSocket endpoint available at ws://<host>:6000\n"
    headers = Headers()
    headers["Content-Type"] = "text/plain; charset=utf-8"
    headers["Content-Length"] = str(len(body))
    headers["Connection"] = "close"
    return Response(426, "Upgrade Required", headers, body)


# ---------------- START ----------------
gyro_bias = calibrate_gyro()

async def main():
    async with websockets.serve(ws_handler, "0.0.0.0", PORT, process_request=process_request):
        print(f"WebSocket server running on port {PORT}")
        await asyncio.Future()


asyncio.run(main())

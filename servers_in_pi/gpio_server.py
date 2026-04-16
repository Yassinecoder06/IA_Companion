from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import RPi.GPIO as GPIO
import smbus
import time

PORT = 6000

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
class GPIOHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        global gyro_enabled

        if self.path != "/gpio":
            self.send_response(404)
            self.end_headers()
            return

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

        data = {
            "buttons": button_states,
            "lights": light_states,
            "gyro_enabled": gyro_enabled,
            "gyro_orientation": gyro_state,
            "raw_velocity": raw_velocity
        }

        response = json.dumps(data).encode()

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(response)


# ---------------- START ----------------
gyro_bias = calibrate_gyro()

server = HTTPServer(("0.0.0.0", PORT), GPIOHandler)

print(f"Server running on port {PORT}")

server.serve_forever()
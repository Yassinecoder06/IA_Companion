import requests
import time

URL = "http://10.32.33.98:6000/gpio"   # change to your Pi IP

while True:
    try:
        r = requests.get(URL, timeout=1)
        data = r.json()

        print("Buttons:", data["buttons"])
        print("Lights:", data["lights"])
        print("Orientation:", data["gyro_orientation"])
        print("Raw Velocity:", data["raw_velocity"])
        print("----")

    except Exception as e:
        print("Connection error:", e)

    time.sleep(0.2) 
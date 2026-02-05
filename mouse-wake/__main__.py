#! /usr/bin/env python3

import subprocess
import time
from selectors import DefaultSelector, EVENT_READ
from evdev import InputDevice, ecodes as e, list_devices

COOLDOWN = 0.5

# Device names to exclude — these report EV_REL but aren't real mice
EXCLUDED_NAMES = {"CEC-toolbox Virtual Input"}
EXCLUDED_PREFIXES = ("DP-",)


def find_mice():
    mice = []
    for path in list_devices():
        try:
            dev = InputDevice(path)
            if dev.name in EXCLUDED_NAMES:
                continue
            if any(dev.name.startswith(p) for p in EXCLUDED_PREFIXES):
                continue
            caps = dev.capabilities()
            if e.EV_REL in caps:
                rel_caps = caps[e.EV_REL]
                if e.REL_X in rel_caps or e.REL_Y in rel_caps:
                    mice.append(dev)
        except Exception:
            continue
    return mice


def tv_is_off():
    try:
        result = subprocess.run(
            ["/usr/bin/cec-toolbox", "state"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() == "0"
    except Exception:
        return False


def tv_on():
    try:
        subprocess.run(["/usr/bin/cec-toolbox", "on"], timeout=10)
    except Exception:
        pass


def main_loop():
    last_cec_check = 0

    mice = find_mice()
    if not mice:
        print("No mouse devices found, waiting...")
        return

    print(f"Monitoring {len(mice)} mouse device(s): {', '.join(m.name for m in mice)}")

    selector = DefaultSelector()
    for mouse in mice:
        selector.register(mouse, EVENT_READ)

    try:
        while True:
            for key, _ in selector.select():
                device = key.fileobj
                try:
                    events = list(device.read())
                except OSError:
                    print(f"Device disconnected: {device.name}")
                    selector.unregister(device)
                    device.close()
                    if not selector.get_map():
                        print("All devices disconnected, restarting discovery...")
                        return
                    continue

                has_movement = any(ev.type == e.EV_REL for ev in events)
                if not has_movement:
                    continue

                now = time.time()
                if (now - last_cec_check) > COOLDOWN:
                    last_cec_check = now
                    if tv_is_off():
                        print("TV is off, turning on")
                        tv_on()
    finally:
        selector.close()


print("starting cec-toolbox mouse wake daemon")

while True:
    try:
        main_loop()
    except Exception as ex:
        print(f"Error in main loop: {ex}")
    time.sleep(5)

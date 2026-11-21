# Роборука V1.2 — ESP32 MPU6050 air-drawing prototype

A self-contained **joystick-like** hand-controlled drawing demonstration for Windows.

This prototype is **separate** from the existing `roboruka_desktop_v0_1` and `code` folders; no prior application files were replaced.

## Contents

- `firmware/Roboruka_V1/Roboruka_V1.ino` — Arduino IDE firmware for ESP32 + MPU6050.
- `roboruka_whiteboard.py` — Python/Tkinter whiteboard controlled over USB Serial.
- `requirements.txt` — Python dependency list.

## Wiring

| MPU6050 | ESP32 |
| --- | --- |
| VCC | **3V3** |
| GND | GND |
| SDA | GPIO **25** |
| SCL | GPIO **33** |

**Hardware safety:** Disconnect USB before soldering. Check for a short between VCC and GND before reconnecting power. Earlier serial diagnostics included `Brownout detector was triggered`; do not disable brownout protection to hide a power fault. Sensor reconnection logic cannot repair unstable power.

## Install and run (Windows)

1. Open `firmware/Roboruka_V1/Roboruka_V1.ino` in Arduino IDE.
2. Select the ESP32 board and its COM port, then upload.
3. Keep the sensor completely still in your comfortable neutral pose during calibration.
4. Install Python 3 (with Tkinter) and the dependency:

   ```powershell
   py -m pip install -r requirements.txt
   ```

5. **Close Arduino Serial Monitor** so the COM port is free.
6. Run from this folder:

   ```powershell
   py roboruka_whiteboard.py
   ```

   If automatic COM selection doesn't work:

   ```powershell
   py roboruka_whiteboard.py --port COM5
   ```

   Test without hardware:

   ```powershell
   py roboruka_whiteboard.py --demo
   ```

## Controls

| Key | Action |
| --- | --- |
| Space | Toggle pen on/off |
| C | Clear the whiteboard |
| R | Recalibrate neutral (hold sensor still) |
| H | Center the *virtual cursor* |
| Esc | Quit |

Tilt from the calibrated neutral orientation sets **cursor velocity**, not absolute position. Return to neutral to stop without recentering.

## Behavior and limitations

- Firmware uses I²C at 100 kHz, gyroscope bias calibration, an accelerometer/gyro complementary filter, a 3° dead zone, and a nonlinear velocity curve.
- USB Serial baud rate: **115200**; JSON line messages at approximately **50 Hz**.
- Firmware reports status packets and retries a disconnected MPU6050.
- The desktop app ignores malformed packets, stops motion if packets are stale (220 ms), and includes a simulated demo mode.
- This version controls only its **own whiteboard canvas**, not the Windows system cursor.
- Absolute yaw and 3D hand translation are not available from an MPU6050 alone; significant motion/tilt can reduce accuracy.
- Python syntax has been checked. The hardware setup and Windows GUI still need testing on a real device.

## Tuning

In the Arduino firmware edit: `MAX_TILT_DEG`, `DEAD_ZONE_DEG`, `MAX_SPEED_PX_S`, `INVERT_X`, and `INVERT_Y`.

This folder is an independent early prototype and is not yet integrated with the existing `roboruka_desktop_v0_1` desktop architecture.

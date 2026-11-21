"""Roboruka V1.2: local USB Serial drawing canvas. Python 3 + pyserial + tkinter.

Usage:
  py roboruka_whiteboard.py
  py roboruka_whiteboard.py --port COM5
  py roboruka_whiteboard.py --demo

Keys: SPACE = pen on/off, C = clear, R = neutral recalibration,
      H = home canvas cursor, ESC = exit.
"""
import argparse
import json
import math
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk

try:
    import serial
    from serial.tools import list_ports
except ImportError as exc:
    raise SystemExit('Install pyserial first: py -m pip install pyserial') from exc


class SerialWorker(threading.Thread):
    def __init__(self, output, commands, port=None, demo=False):
        super().__init__(daemon=True)
        self.output = output
        self.commands = commands
        self.port = port
        self.demo = demo
        self.stop_event = threading.Event()

    def emit(self, data):
        # Only latest motion sample matters; avoid an infinite queue if UI lags.
        if data.get('type') == 'motion' and self.output.qsize() > 100:
            try:
                while self.output.qsize() > 25:
                    self.output.get_nowait()
            except queue.Empty:
                pass
        self.output.put((time.monotonic(), data))

    def choose_ports(self):
        if self.port:
            return [self.port]
        ports = list(list_ports.comports())
        # Prefer devices identifying as common USB serial adapters/ESP boards.
        def score(p):
            name = (p.description + ' ' + (p.manufacturer or '')).lower()
            keywords = ('cp210', 'ch340', 'ch910', 'usb serial', 'silicon labs', 'esp32')
            return 0 if any(word in name for word in keywords) else 1
        ports.sort(key=score)
        return [p.device for p in ports]

    def run(self):
        if self.demo:
            self.run_demo()
            return
        while not self.stop_event.is_set():
            ports = self.choose_ports()
            if not ports:
                self.emit({'type': 'status', 'state': 'no_com_port'})
            for port in ports:
                if self.stop_event.is_set():
                    return
                try:
                    with serial.Serial(port, 115200, timeout=0.12, write_timeout=0.2) as ser:
                        self.emit({'type': 'status', 'state': 'connected_to_' + port})
                        last_data = time.monotonic()
                        while not self.stop_event.is_set():
                            try:
                                while True:
                                    cmd = self.commands.get_nowait()
                                    ser.write(cmd.encode('ascii'))
                            except queue.Empty:
                                pass
                            line = ser.readline()
                            if not line:
                                if time.monotonic() - last_data > 4:
                                    raise ConnectionError('No device messages for 4 seconds')
                                continue
                            try:
                                packet = json.loads(line.decode('utf-8', errors='replace'))
                            except (ValueError, UnicodeDecodeError):
                                continue  # Ignore ESP32 boot text / malformed lines
                            if packet.get('version') != 1 or packet.get('type') not in ('motion', 'status'):
                                continue
                            last_data = time.monotonic()
                            self.emit(packet)
                except (OSError, serial.SerialException, ConnectionError) as exc:
                    self.emit({'type': 'status', 'state': 'disconnected', 'detail': str(exc)})
            self.stop_event.wait(1.5)

    def run_demo(self):
        self.emit({'version': 1, 'type': 'status', 'state': 'ready_demo'})
        start = time.monotonic()
        seq = 0
        while not self.stop_event.is_set():
            t = time.monotonic() - start
            self.emit({
                'version': 1, 'type': 'motion', 'sequence': seq,
                'roll': 15 * math.cos(t * 0.9),
                'pitch': 15 * math.sin(t * 0.7),
                'vx': 160 * math.cos(t * 0.9),
                'vy': 130 * math.sin(t * 0.7),
                'quality': 1,
            })
            seq += 1
            self.stop_event.wait(0.02)


class Whiteboard:
    def __init__(self, root, args):
        self.root = root
        root.title('Роборука — Air Drawing V1.2')
        root.geometry('1060x750')
        root.minsize(700, 480)
        self.events = queue.Queue()
        self.commands = queue.Queue()
        self.worker = SerialWorker(self.events, self.commands, args.port, args.demo)
        self.worker.start()
        self.demo = args.demo

        self.pen = False
        self.vx = self.vy = 0.0
        self.last_motion = 0.0
        self.previous_frame = time.monotonic()
        self.status = 'Connecting…'
        self.x = self.y = None
        self.prev_draw = None
        self.last_seq = -1
        self.quality = 0
        self.roll = self.pitch = 0.0
        self.status_since = 0.0
        self.sensor_ready = False
        self.last_port = ''

        self.toolbar = ttk.Frame(root, padding=8)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        ttk.Button(self.toolbar, text='Pen OFF / ON  [Space]', command=self.toggle_pen).pack(side=tk.LEFT, padx=3)
        ttk.Button(self.toolbar, text='Clear  [C]', command=self.clear).pack(side=tk.LEFT, padx=3)
        ttk.Button(self.toolbar, text='Recalibrate  [R]', command=self.recalibrate).pack(side=tk.LEFT, padx=3)
        ttk.Button(self.toolbar, text='Home  [H]', command=self.home).pack(side=tk.LEFT, padx=3)
        self.pen_label = ttk.Label(self.toolbar, text='PEN OFF')
        self.pen_label.pack(side=tk.RIGHT, padx=10)

        self.canvas = tk.Canvas(root, bg='white', highlightthickness=1,
                                highlightbackground='#d1d5db', cursor='crosshair')
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))
        self.canvas.bind('<Configure>', self.on_resize)
        self.canvas.focus_set()

        self.info = ttk.Label(root, padding=(12, 3), text='Looking for ESP32…')
        self.info.pack(fill=tk.X, side=tk.BOTTOM)
        self.help = ttk.Label(root, padding=(12, 0),
            text='Tilt wrist = cursor speed  •  Neutral = stop  •  Space = draw  •  R = recalibrate  •  Esc = quit')
        self.help.pack(fill=tk.X, side=tk.BOTTOM)

        root.bind_all('<space>', lambda e: self.toggle_pen())
        root.bind_all('<KeyPress-c>', lambda e: self.clear())
        root.bind_all('<KeyPress-C>', lambda e: self.clear())
        root.bind_all('<KeyPress-r>', lambda e: self.recalibrate())
        root.bind_all('<KeyPress-R>', lambda e: self.recalibrate())
        root.bind_all('<KeyPress-h>', lambda e: self.home())
        root.bind_all('<KeyPress-H>', lambda e: self.home())
        root.bind_all('<Escape>', lambda e: self.close())
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.after(16, self.tick)

    def on_resize(self, _event=None):
        if self.x is None:
            self.home()

    def home(self):
        self.x = max(10, self.canvas.winfo_width() / 2)
        self.y = max(10, self.canvas.winfo_height() / 2)
        self.prev_draw = None

    def toggle_pen(self):
        self.pen = not self.pen
        self.pen_label.configure(text='PEN ON — drawing' if self.pen else 'PEN OFF — moving')
        self.prev_draw = None

    def clear(self):
        self.canvas.delete('stroke')
        self.prev_draw = None

    def recalibrate(self):
        self.vx = self.vy = 0
        self.sensor_ready = False
        self.status = 'Recalibrating — hold the MPU6050 completely still'
        self.prev_draw = None
        if not self.demo:
            self.commands.put('R\n')
        else:
            self.sensor_ready = True
            self.status = 'Demo running'

    def close(self):
        self.worker.stop_event.set()
        self.root.destroy()

    def tick(self):
        now = time.monotonic()
        dt = min(now - self.previous_frame, 0.05)
        self.previous_frame = now
        try:
            while True:
                timestamp, packet = self.events.get_nowait()
                if packet['type'] == 'status':
                    state = packet.get('state', 'unknown')
                    self.status = state.replace('_', ' ')
                    if state.startswith('connected_to_'):
                        self.last_port = state.removeprefix('connected_to_')
                        self.sensor_ready = False
                    elif state in ('ready', 'ready_demo'):
                        self.sensor_ready = True
                        self.last_motion = now
                        self.vx = self.vy = 0
                    else:
                        self.sensor_ready = False
                        self.vx = self.vy = 0
                        self.prev_draw = None
                elif packet['type'] == 'motion' and self.sensor_ready:
                    try:
                        vx = float(packet.get('vx', 0))
                        vy = float(packet.get('vy', 0))
                        roll = float(packet.get('roll', 0))
                        pitch = float(packet.get('pitch', 0))
                        quality = int(packet.get('quality', 0))
                    except (TypeError, ValueError):
                        continue
                    if not all(math.isfinite(n) for n in (vx, vy, roll, pitch)):
                        continue
                    self.quality = quality
                    if quality == 1:
                        self.vx = max(-650, min(650, vx))
                        self.vy = max(-650, min(650, vy))
                        self.roll, self.pitch = roll, pitch
                        self.last_motion = timestamp
                    else:
                        self.vx = self.vy = 0
        except queue.Empty:
            pass

        # Fail safe: any lost/late sensor packet stops the virtual cursor.
        active = self.sensor_ready and (now - self.last_motion < 0.22)
        if not active:
            self.vx = self.vy = 0
            self.prev_draw = None

        if self.x is None:
            self.home()
        x0, y0 = self.x, self.y
        w = max(self.canvas.winfo_width(), 20)
        h = max(self.canvas.winfo_height(), 20)
        self.x = min(max(self.x + self.vx * dt, 6), w - 6)
        self.y = min(max(self.y + self.vy * dt, 6), h - 6)

        if active and self.pen and self.prev_draw is not None:
            if abs(self.x - x0) + abs(self.y - y0) > 0.01:
                self.canvas.create_line(x0, y0, self.x, self.y,
                    fill='#1769aa', width=3, capstyle=tk.ROUND,
                    smooth=True, tags='stroke')
        self.prev_draw = (self.x, self.y) if active and self.pen else None
        self.canvas.delete('pointer')
        outline = '#1679bd' if active else '#d97706'
        self.canvas.create_oval(self.x-8, self.y-8, self.x+8, self.y+8,
                                outline=outline, width=2, tags='pointer')
        self.canvas.create_line(self.x-12, self.y, self.x+12, self.y,
                                fill=outline, tags='pointer')
        self.canvas.create_line(self.x, self.y-12, self.x, self.y+12,
                                fill=outline, tags='pointer')

        self.info.configure(text=(
            f"{'DEMO' if self.demo else (self.last_port or 'USB')}  |  "
            f"{self.status}  |  "
            f"Roll {self.roll:+.1f}°  Pitch {self.pitch:+.1f}°  |  "
            f"Velocity ({self.vx:+.0f}, {self.vy:+.0f}) px/s  |  "
            f"{'TRACKING' if active else 'STOPPED / NO DATA'}"
        ))
        self.root.after(16, self.tick)


def main():
    parser = argparse.ArgumentParser(description='Роборука air drawing whiteboard')
    parser.add_argument('--port', help='COM port, e.g. COM5 (default: auto-detect)')
    parser.add_argument('--demo', action='store_true', help='Try the UI with simulated motion')
    args = parser.parse_args()
    root = tk.Tk()
    Whiteboard(root, args)
    root.mainloop()


if __name__ == '__main__':
    main()

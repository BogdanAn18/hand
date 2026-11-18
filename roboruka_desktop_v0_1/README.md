# Roboruka Desktop v0.1

A modular Windows whiteboard prototype built with Python and PySide6. The project includes VS Code launch/debug settings. It currently supports:
- Freehand pen, line, rectangle, ellipse and eraser
- Undo / redo
- Mouse input
- Simulated controller input (keyboard-driven)
- A hardware-independent input-provider interface
- A newline-delimited JSON protocol parser and serial transport skeleton for future ESP32 integration

## Requirements

- Windows 10/11, 64-bit
- Python 3.10 or newer (your installed Python 3.14 is also suitable with current PySide6 wheels)
- Visual Studio Code (recommended editor) with the Microsoft Python extension

## Open in VS Code

1. Extract the ZIP to a normal working folder (not `C:\\Windows\\System32`).
2. In VS Code choose **File → Open Folder...** and open `roboruka_desktop_v0_1`.
3. Open the integrated terminal (**Terminal → New Terminal**).
4. Create a virtual environment using the Python version you actually have installed:

```powershell
py -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

5. Press **F5** and select **Roboruka Desktop** if prompted. The included `.vscode/launch.json` remembers this configuration.

If `py` does not select the intended interpreter, list installed versions with `py -0p`, then use the full executable path, for example:

```powershell
& "$env:LOCALAPPDATA\\Programs\\Python\\Python314\\python.exe" -m venv .venv
```

The actual path may differ; use the path shown by `py -0p` or VS Code's **Python: Select Interpreter** command.

## Run on Windows (without VS Code)

Open PowerShell in this folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

If PowerShell blocks activation, run this once in the same terminal:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Alternatively, use Command Prompt:
```bat
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

## Using the application

- Select a tool in the toolbar.
- Use the mouse to draw on the white canvas.
- Pen thickness and color are available in the toolbar.
- Undo / redo use the toolbar or Ctrl+Z / Ctrl+Y.
- Clear removes all objects (undoable).
- Choose **Input → Simulated controller** to switch to keyboard simulation.
- In simulation mode use **W/A/S/D** to move the pointer, **Space** to toggle drawing, and **Escape** to stop drawing. The simulated pointer is shown as a blue crosshair.
- Switch back to **Input → Mouse** to resume mouse drawing.

## Project structure

```text
roboruka_desktop_v0_1/
├── main.py
├── requirements.txt
├── README.md
├── app/
│   ├── application.py
│   └── config.py
├── ui/
│   ├── main_window.py
│   ├── canvas_widget.py
│   └── toolbar.py
├── core/
│   ├── document.py
│   ├── geometry.py
│   ├── stroke.py
│   └── tools/
│       ├── base.py
│       ├── pen.py
│       ├── shape.py
│       └── eraser.py
├── input/
│   ├── __init__.py
│   ├── provider.py
│   ├── mouse_input.py
│   └── simulator.py
├── motion/
│   ├── processor.py
│   ├── coordinate_mapper.py
│   ├── filters.py
│   └── calibration.py
├── communication/
│   ├── protocol.py
│   ├── messages.py
│   └── serial_manager.py
└── tests/
    ├── test_document.py
    └── test_protocol.py
```

## Architecture notes

The drawing document stores vector-like drawing objects in canvas coordinates. Input providers publish normalized pointer states (0..1); the canvas maps them to its current size. This keeps the drawing engine independent of whether coordinates come from a mouse, simulator, or ESP32.

The serial manager is deliberately a small integration seam, not a claim that the final ESP32 firmware protocol has already been agreed. Protocol v1 currently accepts JSON objects with `version`, `type`, and optional `position`, `orientation`, and `buttons` fields. Confirm coordinate definitions, button semantics, sample rate, and calibration strategy with the firmware before connecting real hardware.

## Run tests

```powershell
pip install pytest
python -m pytest
```

## Build a Windows executable (optional)

```powershell
pip install pyinstaller
pyinstaller --noconfirm --clean --windowed --name Roboruka main.py
```

The executable will be in `dist\Roboruka\` (or `dist\Roboruka.exe`, depending on the PyInstaller version and build mode).

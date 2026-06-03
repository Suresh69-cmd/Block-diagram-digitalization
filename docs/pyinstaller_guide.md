# PyInstaller Guide

PyInstaller converts your Python GUI project into a Windows `.exe`.

## Install

```powershell
pip install pyinstaller
```

## Build the GUI EXE

From inside `control_diagram_digitizer`, run:

```powershell
pyinstaller --onefile --windowed --name ControlDiagramDigitizer gui/app.py
```

Meaning:

- `--onefile`: create one EXE file.
- `--windowed`: do not show a black terminal window behind the GUI.
- `--name`: choose the EXE name.

## Where the EXE is created

```text
dist/ControlDiagramDigitizer.exe
```

## Common problem: file paths

During development, Python runs from your project folder. In EXE form, files are packed differently.

This starter project keeps the GUI simple. Later, if you add model files, place them in a `models/` folder and update the PyInstaller command with `--add-data`.

Example:

```powershell
pyinstaller --onefile --windowed --name ControlDiagramDigitizer --add-data "models;models" gui/app.py
```

On Windows, `--add-data` uses a semicolon between source and destination.


# Beginner Step-by-Step Guide

## 1. Open the project

Open PowerShell and go to the project folder:

```powershell
cd control_diagram_digitizer
```

## 2. Create Git repository

Run:

```powershell
git init
git add .
git commit -m "Initial control diagram digitizer skeleton"
```

If Git asks for your name and email:

```powershell
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"
```

Then run the commit command again.

## 3. Create virtual environment

Run:

```powershell
python -m venv .venv
```

## 4. Activate virtual environment

Run:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate again.

## 5. Install dependencies

The dummy pipeline and GUI use standard Python only. Install dependencies when you are ready to build the EXE:

```powershell
pip install -r requirements.txt
```

## 6. Test dummy pipeline

Run:

```powershell
python main.py --image data/sample/sample_diagram.png
```

Expected result:

```text
Pipeline completed successfully.
Output saved to: ...
```

## 7. Open output JSON

Open:

```text
data/output/latest_output.json
```

You should see blocks, text, connections, and diagram metadata.

## 8. Run GUI

Run:

```powershell
python gui/app.py
```

Click:

1. Browse Image
2. Select `data/sample/sample_diagram.png`
3. Run Pipeline

The JSON output will appear inside the app.

## 9. Run tests

Run:

```powershell
python -m unittest discover -s tests
```

Expected result:

```text
Ran 1 test
OK
```

## 10. Give teammates the module contract

Ask each teammate to return data in the same format as the dummy detector files.

Important files:

- `src/detectors/object_detector.py`
- `src/detectors/text_detector.py`
- `src/detectors/ocr_extractor.py`
- `src/detectors/line_detector.py`

They can replace the dummy logic, but should keep the function names.

## 11. Build EXE

After the GUI works:

```powershell
pip install -r requirements.txt
pyinstaller --onefile --windowed --name ControlDiagramDigitizer gui/app.py
```

Open:

```text
dist/ControlDiagramDigitizer.exe
```

## 12. Final project workflow

Use this order:

1. Collect image.
2. Object detector finds blocks.
3. Text detector finds text boxes.
4. OCR extractor reads text.
5. Line detector finds connections.
6. Integration code combines everything.
7. Schema validator checks JSON quality.
8. GUI displays result.
9. PyInstaller creates EXE.

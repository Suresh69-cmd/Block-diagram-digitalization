# Control Diagram Digitizer

Beginner-friendly integration project for converting a control system block diagram image into a digital JSON representation.

## What this project does now

This starter version uses dummy detector modules so the full pipeline can be tested before the real team modules arrive.

Input:

- Diagram image path

Output:

- Blocks
- Text
- Connections
- Coordinates
- Diagram structure
- JSON file saved in `data/output/`

## Team module contract

Each teammate should eventually replace one dummy file in `src/detectors/`:

- Object Detection Engineer: `object_detector.py`
- Text Detection Engineer: `text_detector.py`
- Low-Resolution Text Extraction Engineer: `ocr_extractor.py`
- Line Detection Engineer: `line_detector.py`

Keep the function names and returned dictionary format the same so integration stays easy.

## Setup

Open PowerShell in this project folder:

```powershell
cd control_diagram_digitizer
```

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies. This is only needed when you are ready to build the EXE:

```powershell
pip install -r requirements.txt
```

## Run the complete dummy pipeline

```powershell
python main.py --image data/sample/sample_diagram.png
```

The output JSON will be saved in:

```text
data/output/latest_output.json
```

## Run the GUI

```powershell
python gui/app.py
```

Use **Browse Image**, select an image, then click **Run Pipeline**.

## Run tests

```powershell
python -m unittest discover -s tests
```

## Build EXE with PyInstaller

Install PyInstaller:

```powershell
pip install pyinstaller
```

Build GUI executable:

```powershell
pyinstaller --onefile --windowed --name ControlDiagramDigitizer gui/app.py
```

Your EXE will appear in:

```text
dist/ControlDiagramDigitizer.exe
```

## Project structure

```text
control_diagram_digitizer/
  main.py
  requirements.txt
  README.md
  docs/
    beginner_steps.md
    pyinstaller_guide.md
  schema/
    diagram_schema.json
  src/
    pipeline.py
    schema_validation.py
    detectors/
      object_detector.py
      text_detector.py
      ocr_extractor.py
      line_detector.py
    integration/
      structure_builder.py
    utils/
      file_io.py
  gui/
    app.py
  data/
    sample/
    output/
  tests/
    test_pipeline.py
```


##  Object Detection Module (YOLO)

This module is responsible for detecting components (blocks) in control/industrial diagrams using a YOLO-based model.

---

###  File Location

```text
src/detectors/object_detector.py
```

---

###  Features

* Sliding window detection for large diagrams
* Global Non-Maximum Suppression (NMS) to remove duplicates
* Edge filtering to discard partial detections
* Class filtering (ignores unwanted classes like connectors)
* Generates structured JSON output
* Saves visualized detection image

---

###  Configuration Parameters

```python
PATCH_SIZE = 832      # Size of each detection patch
STRIDE = 600          # Step size for sliding window
CONF_THRESH = 0.6     # Confidence threshold
IOU_THRESH = 0.50     # NMS threshold
```

---

###  Supported Classes

```python
CLASSES = {
    0: "valve", 
    1: "connector", 
    2: "instrumentation", 
    3: "tank", 
    4: "arrow", 
    5: "inlet/outlet"
}
```

 Note: `"connector"` class is ignored in final output.

---

###  How to Use

```python
from src.detectors.object_detector import run_detector

run_detector(
    input_source="data/sample",     # image or folder
    output_dir="data/output",       # output folder
    weights_path="models/best.pt"   # YOLO weights
)
```

---

###  Input

* Single image OR folder of images

---

###  Output

For each image:

```text
data/output/
  ├── <image_name>_output.json
  ├── <image_name>_visualized.jpg
```

---



---



###  Dependencies

Add to `requirements.txt`:

```text
ultralytics
opencv-python
```

---

###  Exclusions

* Model weights (`.pt`) are NOT included in repo
* Output files are generated dynamically (not stored in repo)

---


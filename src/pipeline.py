from pathlib import Path

from src.detectors.line_detector import detect_lines
from src.detectors.object_detector import detect_blocks
from src.detectors.ocr_extractor import extract_text_values
from src.detectors.text_detector import detect_text_regions
from src.integration.structure_builder import build_diagram_structure
from src.schema_validation import validate_diagram_json


def run_pipeline(image_path: str) -> dict:
    image = Path(image_path)
    if not image.exists():
        raise FileNotFoundError(f"Input image not found: {image}")

    blocks = detect_blocks(image)
    text_regions = detect_text_regions(image)
    text_items = extract_text_values(image, text_regions)
    connections = detect_lines(image, blocks)

    diagram_json = build_diagram_structure(
        image_path=str(image),
        blocks=blocks,
        text_items=text_items,
        connections=connections,
    )

    validate_diagram_json(diagram_json)
    return diagram_json

#dfghj
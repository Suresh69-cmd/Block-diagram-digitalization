from pathlib import Path


def detect_text_regions(image_path: Path) -> list[dict]:
    """Dummy text detector. Replace this with detected text bounding boxes."""
    return [
        {"id": "text_1", "bbox": {"x": 20, "y": 140, "width": 45, "height": 25}, "confidence": 0.99},
        {"id": "text_2", "bbox": {"x": 270, "y": 140, "width": 60, "height": 25}, "confidence": 0.99},
        {"id": "text_3", "bbox": {"x": 535, "y": 140, "width": 45, "height": 25}, "confidence": 0.99},
    ]


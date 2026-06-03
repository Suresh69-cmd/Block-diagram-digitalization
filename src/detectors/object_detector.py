from pathlib import Path


def detect_blocks(image_path: Path) -> list[dict]:
    """Dummy object detector. Replace this with the real object detection model output."""
    return [
        {
            "id": "block_1",
            "type": "sum",
            "label": "Sum",
            "bbox": {"x": 80, "y": 120, "width": 70, "height": 70},
            "confidence": 0.99,
        },
        {
            "id": "block_2",
            "type": "transfer_function",
            "label": "G(s)",
            "bbox": {"x": 240, "y": 120, "width": 120, "height": 70},
            "confidence": 0.99,
        },
        {
            "id": "block_3",
            "type": "output",
            "label": "Output",
            "bbox": {"x": 460, "y": 135, "width": 60, "height": 40},
            "confidence": 0.99,
        },
    ]


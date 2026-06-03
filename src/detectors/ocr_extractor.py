from pathlib import Path


def extract_text_values(image_path: Path, text_regions: list[dict]) -> list[dict]:
    """Dummy OCR extractor. Replace this with the low-resolution text extraction output."""
    dummy_values = ["R(s)", "G(s)", "C(s)"]
    text_items = []

    for index, region in enumerate(text_regions):
        text_items.append(
            {
                "id": region["id"],
                "text": dummy_values[index] if index < len(dummy_values) else "",
                "bbox": region["bbox"],
                "confidence": region["confidence"],
            }
        )

    return text_items


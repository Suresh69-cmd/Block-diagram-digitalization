from pathlib import Path


def detect_lines(image_path: Path, blocks: list[dict]) -> list[dict]:
    """Dummy line detector. Replace this with real connection detection output."""
    return [
        {
            "id": "conn_1",
            "from": "input",
            "to": "block_1",
            "points": [{"x": 20, "y": 155}, {"x": 80, "y": 155}],
            "arrow": True,
            "confidence": 0.99,
        },
        {
            "id": "conn_2",
            "from": "block_1",
            "to": "block_2",
            "points": [{"x": 150, "y": 155}, {"x": 240, "y": 155}],
            "arrow": True,
            "confidence": 0.99,
        },
        {
            "id": "conn_3",
            "from": "block_2",
            "to": "block_3",
            "points": [{"x": 360, "y": 155}, {"x": 460, "y": 155}],
            "arrow": True,
            "confidence": 0.99,
        },
    ]


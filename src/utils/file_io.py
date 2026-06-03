import json
from pathlib import Path


def save_json(data: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def load_json(input_path: Path) -> dict:
    with input_path.open("r", encoding="utf-8") as file:
        return json.load(file)


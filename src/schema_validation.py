def validate_diagram_json(diagram_json: dict) -> None:
    required_top_level_keys = ["metadata", "blocks", "text", "connections", "diagram"]
    for key in required_top_level_keys:
        if key not in diagram_json:
            raise ValueError(f"Missing required top-level key: {key}")

    for block in diagram_json["blocks"]:
        _require_keys(block, ["id", "type", "label", "bbox", "confidence"], "block")
        _validate_bbox(block["bbox"], f"block {block['id']}")

    for text_item in diagram_json["text"]:
        _require_keys(text_item, ["id", "text", "bbox", "confidence"], "text item")
        _validate_bbox(text_item["bbox"], f"text item {text_item['id']}")

    for connection in diagram_json["connections"]:
        _require_keys(connection, ["id", "from", "to", "points", "arrow", "confidence"], "connection")
        if len(connection["points"]) < 2:
            raise ValueError(f"Connection {connection['id']} must contain at least two points")


def _require_keys(data: dict, keys: list[str], item_name: str) -> None:
    for key in keys:
        if key not in data:
            raise ValueError(f"Missing {key} in {item_name}")


def _validate_bbox(bbox: dict, item_name: str) -> None:
    _require_keys(bbox, ["x", "y", "width", "height"], f"{item_name} bbox")
    if bbox["width"] < 0 or bbox["height"] < 0:
        raise ValueError(f"{item_name} bbox width and height must be non-negative")

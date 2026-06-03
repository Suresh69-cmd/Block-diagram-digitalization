from datetime import datetime, timezone


def build_diagram_structure(
    image_path: str,
    blocks: list[dict],
    text_items: list[dict],
    connections: list[dict],
) -> dict:
    return {
        "metadata": {
            "schema_version": "1.0.0",
            "source_image": image_path,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        "blocks": blocks,
        "text": text_items,
        "connections": connections,
        "diagram": {
            "type": "control_system_block_diagram",
            "block_count": len(blocks),
            "text_count": len(text_items),
            "connection_count": len(connections),
        },
    }


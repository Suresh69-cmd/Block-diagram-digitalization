import argparse
from pathlib import Path

from src.pipeline import run_pipeline
from src.utils.file_io import save_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Digitize a control system block diagram image.")
    parser.add_argument("--image", required=True, help="Path to the input diagram image.")
    parser.add_argument(
        "--output",
        default="data/output/latest_output.json",
        help="Path where output JSON should be saved.",
    )
    args = parser.parse_args()

    result = run_pipeline(args.image)
    output_path = Path(args.output)
    save_json(result, output_path)

    print(f"Pipeline completed successfully.")
    print(f"Output saved to: {output_path.resolve()}")


if __name__ == "__main__":
    main()


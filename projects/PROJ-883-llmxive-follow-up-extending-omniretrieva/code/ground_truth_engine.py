"""Ground‑truth engine."""
import argparse
import json
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    input_path = paths.path(args.input)
    output_path = paths.path(args.output)

    if not input_path.is_file():
        log.warning("Input file %s not found.", input_path)
        data = []
    else:
        with input_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

    for entry in data:
        if "ground_truth_plan" not in entry:
            entry["ground_truth_plan"] = None

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    log.info("Ground‑truth processing complete.")

if __name__ == "__main__":
    main()

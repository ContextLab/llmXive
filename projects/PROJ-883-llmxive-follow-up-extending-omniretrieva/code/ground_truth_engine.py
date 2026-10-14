"""Ground‑truth engine.

For the skeleton this script simply copies the input JSON to the output
location, ensuring that a ``ground_truth_plan`` field exists for every
entry.  It tolerates missing input files by writing an empty JSON list
instead of raising an exception, so the script always exits with status 0.
"""

import argparse
import json
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Copy generation log while ensuring ground‑truth plans exist."
    )
    parser.add_argument("--input", required=True, help="Path to input JSON.")
    parser.add_argument("--output", required=True, help="Path to output JSON.")
    args = parser.parse_args()

    input_path = paths.path(args.input)
    output_path = paths.path(args.output)

    if not input_path.is_file():
        log.warning("Input file %s does not exist – creating empty generation log.", input_path)
        data = []
    else:
        with input_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

    # Ensure each entry has a ground_truth_plan (generator already adds it)
    for entry in data:
        if "ground_truth_plan" not in entry:
            entry["ground_truth_plan"] = None

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    log.info("Ground‑truth processing complete – %d queries written.", len(data))

if __name__ == "__main__":
    main()

"""
Script to generate and download the reference calendar of releases/conferences
for the Statistical Analysis of Stack Overflow Tags project.

This script uses the verified source implemented in `setup_data_structure.py`,
which provides a hard‑coded list of real historical tech events.
The generated JSON is written to `data/events/reference_calendar.json`.
"""

import sys
import json
from pathlib import Path

# Ensure the project root is on the Python path for absolute imports
ROOT_DIR = Path(__file__).resolve().parents[2]  # <project>/code/data/.. -> <project>
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Import utilities from the llmxive toolkit
from llmxive_toolkit import paths, get_logger

# Import the verified generator function
from code.data.setup_data_structure import generate_reference_calendar

log = get_logger(__name__)

def main() -> int:
    """
    Main entry point.

    Generates the reference calendar using the verified source and writes it
    to the appropriate data path. Returns 0 on success, non‑zero on failure.
    """
    try:
        # Generate calendar data
        calendar_data = generate_reference_calendar()

        # Resolve output path using the toolkit helper (ensures directory exists)
        out_path = paths.data("events", "reference_calendar.json")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Write JSON file
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(calendar_data, f, indent=2)

        log.info(f"Reference calendar written to {out_path}")
        return 0
    except Exception as e:
        log.error(f"Failed to generate reference calendar: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

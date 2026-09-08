"""
generate_validation_config.py
------------------------------

This script creates the validation configuration file required by the
external validation step (US3). It reads the global configuration (via
`config.get_config`) to obtain the `top_n` parameter, which defaults to
10 if not present, and writes a JSON file at
`data/results/validation_config.json` with the following structure:

    {
        "top_n": <int>
    }

The script can be executed directly:

    python code/validate/generate_validation_config.py

It will create the `data/results/` directory if it does not already exist.
"""

import json
import os
from pathlib import Path

# Import the configuration loader from the project's config module.
from config import get_config

def generate_validation_config(output_path: Path) -> None:
    """
    Generate the validation configuration JSON file.

    Parameters
    ----------
    output_path : Path
        The file path where the JSON configuration will be written.
    """
    # Ensure the parent directory exists.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load the global configuration; fall back to default if missing.
    cfg = get_config()
    top_n = cfg.get("top_n", 10)

    # Prepare the JSON payload.
    payload = {"top_n": int(top_n)}

    # Write the JSON file with pretty formatting.
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"Validation config written to {output_path}")

def main() -> None:
    """
    Entry point for the script when executed as a module.
    """
    # Define the output location relative to the repository root.
    output_file = Path("data") / "results" / "validation_config.json"
    generate_validation_config(output_file)

if __name__ == "__main__":
    main()

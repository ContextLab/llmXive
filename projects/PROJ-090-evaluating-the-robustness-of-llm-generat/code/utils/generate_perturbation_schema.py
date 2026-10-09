"""
Utility script to generate the JSON version of the perturbation candidate schema
from its canonical YAML definition.

This script reads ``contracts/perturbation_schema.yaml`` and writes the
equivalent JSON schema to ``contracts/perturbation_schema.json``.
It is used by task **T008a** to guarantee that the JSON schema stays
consistent with the YAML source.
"""

import json
import sys
from pathlib import Path

try:
    import yaml  # PyYAML
except ImportError as exc:
    print(
        "PyYAML is required to run this script. Install it via the project requirements.",
        file=sys.stderr,
    )
    raise exc

def _project_root() -> Path:
    """
    Return the absolute path to the project root directory.

    The script lives in ``code/utils``; the project root is two levels up.
    """
    return Path(__file__).resolve().parents[2]

def main() -> None:
    """Convert the YAML schema to JSON and write it to the contract location."""
    root = _project_root()
    yaml_path = root / "contracts" / "perturbation_schema.yaml"
    json_path = root / "contracts" / "perturbation_schema.json"

    if not yaml_path.is_file():
        print(f"YAML schema not found at {yaml_path}", file=sys.stderr)
        sys.exit(1)

    # Load YAML safely
    with yaml_path.open("r", encoding="utf-8") as f:
        schema_data = yaml.safe_load(f)

    # Write JSON with pretty formatting
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(schema_data, f, indent=2, ensure_ascii=False)

    print(f"Generated JSON schema at {json_path}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
Validate `solvents.yaml` against the JSON Schema defined in `contracts/solvent.schema.yaml`.

Exits with code 0 if validation succeeds, otherwise prints errors to stderr and exits with code 1.
"""
import sys
from pathlib import Path

import yaml
from jsonschema import Draft7Validator

def load_yaml(path: Path):
    """Load a YAML file and return its contents."""
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    # Resolve paths relative to the repository root
    repo_root = Path(__file__).resolve().parents[2]
    schema_path = repo_root / "contracts" / "solvent.schema.yaml"
    data_path = repo_root / "data" / "chemicals" / "solvents.yaml"

    try:
        schema = load_yaml(schema_path)
        data = load_yaml(data_path)
    except Exception as exc:
        print(f"Error loading files: {exc}", file=sys.stderr)
        sys.exit(1)

    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))

    if errors:
        print("Validation failed with the following errors:", file=sys.stderr)
        for err in errors:
            location = "/".join(str(p) for p in err.path)
            print(f"- {location}: {err.message}", file=sys.stderr)
        sys.exit(1)

    print("solvents.yaml successfully validated against solvent.schema.yaml.")
    sys.exit(0)

if __name__ == "__main__":
    main()

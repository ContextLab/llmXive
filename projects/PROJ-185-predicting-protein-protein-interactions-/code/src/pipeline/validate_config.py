"""
Configuration validation script for the PROJ-185 pipeline.

This script validates the `species.yaml` and `parameters.yaml` files located in
`src/config/` against the JSON Schema defined in `contracts/config.schema.yaml`.
It exits with status code 0 on success and non‑zero on validation failure,
printing any schema errors to stderr.
"""

import sys
from pathlib import Path

import yaml
from jsonschema import Draft7Validator, SchemaError, ValidationError

def _load_yaml(path: Path):
    """Load a YAML file and return its Python representation."""
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _validate_instance(schema: dict, instance: dict, filename: str) -> None:
    """Validate a single instance against the provided schema."""
    try:
        validator = Draft7Validator(schema)
    except SchemaError as e:
        print(f"Schema error while loading config schema: {e}", file=sys.stderr)
        sys.exit(1)

    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    if errors:
        for error in errors:
            # Build a human‑readable location string
            location = ".".join(str(p) for p in error.path) if error.path else "(root)"
            print(
                f"[{filename}] Validation error at {location}: {error.message}",
                file=sys.stderr,
            )
        sys.exit(1)

def main() -> None:
    """
    Entry point for the validation script.

    The repository layout is assumed to be:
    - project_root/
        - src/
            - config/
                - species.yaml
                - parameters.yaml
        - contracts/
            - config.schema.yaml
    """
    # Resolve paths relative to this file's location
    project_root = Path(__file__).resolve().parents[2]
    config_dir = project_root / "src" / "config"
    schema_path = project_root / "contracts" / "config.schema.yaml"

    # Load the schema
    if not schema_path.is_file():
        print(f"Schema file not found: {schema_path}", file=sys.stderr)
        sys.exit(1)

    schema = _load_yaml(schema_path)

    # Validate each config file
    for cfg_name in ("species.yaml", "parameters.yaml"):
        cfg_path = config_dir / cfg_name
        if not cfg_path.is_file():
            print(f"Config file not found: {cfg_path}", file=sys.stderr)
            sys.exit(1)

        config_data = _load_yaml(cfg_path)
        _validate_instance(schema, config_data, cfg_name)

    print("All configuration files passed schema validation.")

if __name__ == "__main__":
    main()

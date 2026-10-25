"""
validate_schema.py
------------------
Small utility that validates each contract schema in the ``contracts`` directory
against a minimal dummy instance that satisfies the required fields.

The script exits with status code 0 if *all* schemas validate successfully.
It writes a concise log file to ``logs/schema_validation.log`` indicating the
outcome for each schema.

This fulfills Task T002's verification requirement.
"""

import json
import logging
from pathlib import Path

import yaml
import jsonschema

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #

def load_yaml_schema(schema_path: Path) -> dict:
    """Load a YAML schema file."""
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def dummy_instance_for_schema(schema: dict) -> dict:
    """
    Build a minimal instance that satisfies the ``required`` fields of a JSON schema.

    The function inspects each required property, looks at its declared ``type``,
    and supplies a simple value that conforms to constraints such as ``minimum``,
    ``pattern`` or ``format``.

    This is **not** a full‑fledged generator – it only needs to produce something
    that passes ``jsonschema.validate`` for the purposes of contract testing.
    """
    instance = {}
    required = schema.get("required", [])
    properties = schema.get("properties", {})

    for field in required:
        prop = properties.get(field, {})
        field_type = prop.get("type")

        # Strings – handle common patterns / formats
        if field_type == "string":
            fmt = prop.get("format")
            pattern = prop.get("pattern")
            if pattern:
                # Very simple heuristic: if the pattern looks like a SHA‑256 hex, use 64 'a's
                if "^[a-f0-9]{64}$" in pattern:
                    instance[field] = "a" * 64
                else:
                    instance[field] = "example"
            elif fmt == "date-time":
                instance[field] = "2023-01-01T00:00:00Z"
            elif fmt == "date":
                instance[field] = "2023-01-01"
            else:
                instance[field] = "example"

        # Numbers / integers – respect ``minimum`` when present
        elif field_type in ("number", "integer"):
            minimum = prop.get("minimum")
            if minimum is not None:
                # Use the minimum if it is non‑negative, otherwise use 1
                instance[field] = max(minimum, 1)
            else:
                instance[field] = 1

        # Booleans
        elif field_type == "boolean":
            instance[field] = False

        # Objects – provide an empty dict (acceptable when no required sub‑fields)
        elif field_type == "object":
            instance[field] = {}

        # Fallback
        else:
            instance[field] = None

    return instance


# --------------------------------------------------------------------------- #
# Main validation routine
# --------------------------------------------------------------------------- #

def main() -> None:
    """Validate all contract schemas and write a log file."""
    # Ensure the logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "schema_validation.log"

    logger = logging.getLogger("schema_validation")
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    contracts_dir = Path("contracts")
    schema_files = list(contracts_dir.glob("*.schema.yaml"))

    if not schema_files:
        logger.error("No schema files found in %s", contracts_dir)
        raise FileNotFoundError("No schema files to validate.")

    all_ok = True
    for schema_file in schema_files:
        try:
            schema = load_yaml_schema(schema_file)
            dummy = dummy_instance_for_schema(schema)
            jsonschema.validate(instance=dummy, schema=schema)
            logger.info("Schema %s validated successfully.", schema_file.name)
        except Exception as exc:  # pylint: disable=broad-except
            all_ok = False
            logger.error(
                "Validation failed for %s: %s", schema_file.name, str(exc)
            )

    if all_ok:
        logger.info("All contract schemas validated successfully.")
    else:
        logger.error("One or more schema validations failed.")
        # Exit with non‑zero status to signal failure to the CI runner
        raise SystemExit(1)


if __name__ == "__main__":
    main()
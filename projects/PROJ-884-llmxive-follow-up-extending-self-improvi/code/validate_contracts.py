"""
Validate JSON‑Schema contract files for the llmXive BES pipeline.

This script loads the dataset and output schema YAML files using
``yaml.safe_load`` and exits with status 0 if both are valid.
It writes a tiny JSON report to ``data/processed/contract_validation.json``
indicating success.  The script is intended to be run as part of the
quick‑start validation step:

    python -m code.validate_contracts

If any schema cannot be parsed, the exception propagates and the script
exits with a non‑zero status, causing the task verification to fail.
"""

import json
import sys
from pathlib import Path

import yaml

# Use the toolkit's path helpers to locate contract files and output location
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _load_schema(schema_path: Path) -> dict:
    """Load a YAML schema file, raising any parsing errors."""
    log.info(f"Loading schema from {schema_path}")
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_contracts() -> bool:
    """
    Load and validate the dataset and output JSON‑Schema files.

    Returns:
        True if both schemas are loaded without error.
    Raises:
        yaml.YAMLError or OSError if a file cannot be read or parsed.
    """
    # Resolve contract file locations relative to the project root
    dataset_schema_path = paths.contracts("dataset.schema.yaml")
    output_schema_path = paths.contracts("output.schema.yaml")

    # Load schemas – any exception bubbles up and will cause a non‑zero exit
    _load_schema(dataset_schema_path)
    _load_schema(output_schema_path)

    log.info("Both contract schemas loaded successfully.")
    return True

def _write_report(success: bool) -> None:
    """Write a minimal JSON report indicating validation outcome."""
    report_path = paths.processed("contract_validation.json")
    report = {
        "dataset_schema_valid": success,
        "output_schema_valid": success,
        "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z"
    }
    # Ensure the directory exists
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    log.info(f"Validation report written to {report_path}")

def main() -> None:
    """Entry point for ``python -m code.validate_contracts``."""
    try:
        success = validate_contracts()
    except Exception as exc:
        log.error(f"Schema validation failed: {exc}")
        # Re‑raise to ensure a non‑zero exit status
        raise
    else:
        _write_report(success)

if __name__ == "__main__":
    # When executed as a script, run the validation and exit with
    # appropriate status code.
    try:
        main()
    except Exception:
        sys.exit(1)
    else:
        sys.exit(0)

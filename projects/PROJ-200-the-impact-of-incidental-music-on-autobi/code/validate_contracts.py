"""
Contract Validation Script

This script validates the JSON Schema definitions located in the
``contracts`` directory. It ensures that the schemas themselves are
syntactically correct according to Draft‑07 and that the required
definitions are present as stipulated in ``spec.md``.
"""

import sys
from pathlib import Path

import yaml
from jsonschema import Draft7Validator, SchemaError

def load_schema(schema_path: Path) -> dict:
    """Load a YAML schema file."""
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_schema(schema: dict, name: str) -> None:
    """
    Validate a JSON Schema using jsonschema's Draft7Validator.

    Raises:
        SchemaError: If the schema is not a valid Draft‑07 schema.
    """
    try:
        Draft7Validator.check_schema(schema)
    except SchemaError as exc:
        raise SchemaError(f"Schema validation failed for {name}: {exc}") from exc

def ensure_required_definitions(schema: dict, required_defs: set, name: str) -> None:
    """Confirm that all required top‑level definitions exist."""
    defs = set(schema.get("definitions", {}).keys())
    missing = required_defs - defs
    if missing:
        raise AssertionError(
            f"Schema {name} is missing required definitions: {', '.join(sorted(missing))}"
        )

def main() -> int:
    """Entry point for command‑line execution."""
    project_root = Path(__file__).resolve().parents[1]  # <project>/code/..
    contracts_dir = project_root / "contracts"

    dataset_schema_path = contracts_dir / "dataset.schema.yaml"
    output_schema_path = contracts_dir / "output.schema.yaml"

    # Load schemas
    dataset_schema = load_schema(dataset_schema_path)
    output_schema = load_schema(output_schema_path)

    # Validate schemas themselves
    validate_schema(dataset_schema, "dataset.schema.yaml")
    validate_schema(output_schema, "output.schema.yaml")

    # Ensure required definitions per spec.md
    required_dataset_defs = {
        "Track",
        "CohortListen",
        "MemoryCue",
        "AggregatedMetric",
    }
    required_output_defs = {
        "RegressionResults",
        "SensitivityAnalysis",
        "PermutationResults",
    }

    ensure_required_definitions(dataset_schema, required_dataset_defs, "dataset.schema.yaml")
    ensure_required_definitions(output_schema, required_output_defs, "output.schema.yaml")

    print("✅ All contract schemas are valid and contain required definitions.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

"""Validate data contract schemas against minimal sample instances.

This script loads each ``*.schema.yaml`` file located in
``specs/001-structural-mismatch-cost/contracts`` and validates a
handcrafted, minimal instance that satisfies the schema.  It exits with
``0`` on success and ``1`` on any validation failure.
"""

import sys
from pathlib import Path

import yaml
from jsonschema import Draft7Validator, ValidationError
from llmxive_toolkit import get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Minimal valid instances for each schema.  They contain only the required
# fields defined in the corresponding schema file.
# ----------------------------------------------------------------------
SAMPLE_INSTANCES = {
    "query_instance.schema.yaml": {
        "query_id": "q-001",
        "source_type": "text",
        "complexity_level": 1,
        "ground_truth_plan": "plan-A",
    },
    "execution_log.schema.yaml": {
        "query_id": "q-001",
        "latency_ms": 123.4,
        "success_flag": True,
    },
    "execution_metric.schema.yaml": {
        "query_id": "q-001",
        "latency_ms": 123.4,
    },
    "statistics-result.schema.yaml": {
        "source_type": "graph",
        "complexity_category": "high",
        "mean_delta_latency": 45.6,
        "std_delta_latency": 5.2,
        "n_samples": 30,
        "anova_f_statistic": 4.3,
        "anova_p_value": 0.032,
        "interaction_significant": True,
        "segmented_regression_knee_point": 3.0,
        "segmented_regression_p_value": 0.021,
    },
}

def load_schema(schema_path: Path) -> dict:
    """Load a YAML schema file."""
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_instance(schema: dict, instance: dict, name: str) -> None:
    """Validate a JSON instance against a Draft‑7 schema."""
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    if errors:
        for error in errors:
            log.error(f"Validation error in {name}: {error.message}")
        raise ValidationError(f"{name} does not conform to its schema.")
    else:
        log.info(f"{name} is valid.")

def main() -> int:
    """Validate all contract schemas."""
    contracts_dir = (
        Path(__file__).resolve().parents[1]
        / "specs"
        / "001-structural-mismatch-cost"
        / "contracts"
    )
    if not contracts_dir.is_dir():
        log.error("Contracts directory not found: %s", contracts_dir)
        return 1

    for schema_file in contracts_dir.glob("*.schema.yaml"):
        schema = load_schema(schema_file)
        sample = SAMPLE_INSTANCES.get(schema_file.name)
        if sample is None:
            log.warning(
                "No sample instance provided for %s – skipping validation.",
                schema_file.name,
            )
            continue
        try:
            validate_instance(schema, sample, schema_file.name)
        except ValidationError:
            log.error("Schema %s failed validation.", schema_file.name)
            return 1

    log.info("All schemas validated successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
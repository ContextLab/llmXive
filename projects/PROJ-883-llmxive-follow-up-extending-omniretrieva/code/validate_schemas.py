import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft7Validator, ValidationError
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def load_schema(schema_path: Path) -> dict:
    """Load a JSON‑Schema YAML file."""
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_instance(schema: dict, instance: dict, name: str) -> None:
    """Validate a single instance against its schema and log the result."""
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    if errors:
        log.error(f"Validation failed for {name}:")
        for err in errors:
            log.error(f"  - {err.message} (at {list(err.path)})")
        raise ValidationError(f"{name} instance does not conform to schema")
    else:
        log.info(f"{name} instance is valid.")

def main() -> int:
    # Resolve schema locations inside the specs directory
    contracts_dir = paths.specs("001-structural-mismatch-cost", "contracts")
    schemas = {
        "query_instance": contracts_dir / "query_instance.schema.yaml",
        "execution_log": contracts_dir / "execution_log.schema.yaml",
        "execution_metric": contracts_dir / "execution_metric.schema.yaml",
        "statistics_result": contracts_dir / "statistics-result.schema.yaml",
    }

    # Load each schema
    loaded_schemas = {k: load_schema(p) for k, p in schemas.items()}

    # Sample instances that conform to the schemas
    samples = {
        "query_instance": {
            "query_id": "q123",
            "logical_plan": "SELECT * FROM articles WHERE title LIKE '%AI%'",
            "source_type": "text",
            "complexity_level": 2,
            "ground_truth_plan": "index_scan -> filter",
        },
        "execution_log": {
            "query_id": "q123",
            "source_type": "text",
            "complexity_level": 2,
            "latency_ms": 123.4,
            "translation_error": False,
            "success_flag": True,
            "synthetic_flag": 0,
            "throttling_mode": "cgroups",
        },
        "execution_metric": {
            "query_id": "q123",
            "latency_ms": 123.4,
            "translation_error": False,
            "timeout_flag": False,
        },
        "statistics_result": {
            "cutoff": 3,
            "spike_point": 2.5,
            "slope_change": 1.8,
        },
    }

    # Perform validation
    for name, instance in samples.items():
        schema = loaded_schemas[name]
        try:
            validate_instance(schema, instance, name)
        except ValidationError as e:
            log.error(str(e))
            return 1

    log.info("All sample instances validated successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

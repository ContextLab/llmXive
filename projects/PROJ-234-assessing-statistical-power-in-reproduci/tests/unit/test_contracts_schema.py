"""
Unit tests for contract schema validation.

This test loads each YAML schema file in the `contracts/` directory,
constructs a minimal valid instance based on the schema's required
fields, and validates the instance with `jsonschema.Draft7Validator`.
"""

import json
import pathlib
import datetime

import yaml
from jsonschema import Draft7Validator, ValidationError

# Helper to load a YAML schema file
def load_schema(schema_path: pathlib.Path) -> dict:
    with schema_path.open("r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    assert isinstance(schema, dict), f"Schema at {schema_path} is not a dict"
    return schema

# Minimal valid instances for each schema
def minimal_dataset_metadata():
    return {
        "dataset_id": 1,
        "name": "Test Dataset",
        "download_count": 10,
        "task_type": "Supervised Classification",
    }

def minimal_power_audit_result():
    return {
        "dataset_id": 1,
        "observed_power": 0.5,
        "mdes": 0.2,
        "threshold_met": True,
        "status": "success",
    }

def minimal_extracted_params():
    return {
        "dataset_id": 1,
        "sample_size": 100,
        "effect_size": 0.5,
        "metric_type": "Cohen's d",
        "source_url": "https://example.org/article.pdf",
        "status": "success",
    }

def minimal_report():
    now_iso = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    return {
        "report_metadata": {
            "generated_at": now_iso,
            "pipeline_version": "0.1.0",
            "total_datasets_analyzed": 1,
        },
        "dataset_ingestion_summary": {
            "total_fetched": 1,
            "total_filtered": 1,
            "type_distribution": {"binary": 1},
        },
        "extraction_statistics": {
            "success_rate": 1.0,
            "failure_reasons": {"paywalled": 0, "unparseable": 0, "insufficient_data": 0, "skipped_pre_fetch": 0},
            "sensitivity_delta": {
                "full_text_rate": 1.0,
                "combined_rate": 1.0,
                "delta": 0.0,
            },
        },
        "observed_power_results": {
            "histogram_path": "figures/power_histogram.png",
            "fraction_below_threshold": 0.0,
            "count_below_threshold": 0,
            "total_count": 1,
        },
        "mdes_results": {
            "histogram_path": "figures/mdes_histogram.png",
            "summary_statistics": {
                "median": 0.2,
                "iqr": 0.1,
                "min": 0.1,
                "max": 0.3,
            },
        },
        "success_metrics": {
            "observed_power_below_threshold": 0.0,
            "mdes_above_threshold": 1.0,
        },
        "disclaimer": "Observed power is a monotone function of the p-value and should not be used for post‑hoc validation (Hoenig & Heisey).",
    }

# Mapping of schema filenames to their minimal instances
SCHEMA_INSTANCES = {
    "dataset_metadata.schema.yaml": minimal_dataset_metadata,
    "power_audit_result.schema.yaml": minimal_power_audit_result,
    "extracted_params.schema.yaml": minimal_extracted_params,
    "report.schema.yaml": minimal_report,
}

def test_schemas_validate():
    """
    Load each schema, construct a minimal valid instance, and validate it.
    """
    contracts_dir = pathlib.Path(__file__).resolve().parents[2] / "contracts"
    for schema_file, instance_factory in SCHEMA_INSTANCES.items():
        schema_path = contracts_dir / schema_file
        assert schema_path.is_file(), f"Schema file missing: {schema_path}"
        schema = load_schema(schema_path)

        # Ensure the schema itself is a valid Draft‑7 schema
        validator = Draft7Validator(schema)

        instance = instance_factory()
        try:
            validator.validate(instance)
        except ValidationError as e:
            raise AssertionError(
                f"Validation failed for schema {schema_file} with instance {json.dumps(instance)}: {e.message}"
            ) from e
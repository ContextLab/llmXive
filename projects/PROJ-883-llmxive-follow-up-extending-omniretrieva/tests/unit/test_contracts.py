"""
Unit tests for the contract schema files.
Each schema is loaded with PyYAML and a sample instance is validated
against it using jsonschema. The test also ensures that deprecated
schema files are not present.
"""
import pathlib
import yaml
import jsonschema
import pytest

# Base directory for the contracts
CONTRACTS_DIR = pathlib.Path(__file__).resolve().parents[2] / "specs" / "001-structural-mismatch-cost" / "contracts"

# List of required schema files and a minimal valid instance for each
SCHEMAS = {
    "query_instance.schema.yaml": {
        "query_id": "q_1_123",
        "source_type": "text",
        "complexity_level": 2,
        "logical_plan": {"steps": ["op1", "op2"]},
        "ground_truth_plan": "plan_text_2",
    },
    "execution_log.schema.yaml": {
        "query_id": "q_1_123",
        "source_type": "graph",
        "complexity_level": 3,
        "latency_ms": 45.6,
        "timestamp": "2026-10-15T12:00:00Z",
        "translation_error": False,
        "success_flag": True,
        "timeout_flag": False,
        "synthetic_flag": 0,
        "throttling_mode": "cgroups",
    },
    "execution_metric.schema.yaml": {
        "query_id": "q_1_123",
        "latency_ms": 45.6,
        "mismatch_flag": False,
        "delta_latency": 5.2,
        "engine_version": "sqlite-3.41",
        "throttle_config": "2 cores, 7 GB",
    },
    "statistics_result.schema.yaml": {
        "cutoff": 3,
        "spike_point": 2.0,
        "slope_change": 1.5,
    },
}

# Deprecated filenames that must not exist
DEPRECATED = [
    "analysis_result.schema.yaml",
    "gam_results.schema.yaml",
    "execution_log.schema.yaml_",
    "execution_metrics.schema.yaml",
    "execution-log.schema.yaml",
    "query_result.schema.yaml",
]

def test_deprecated_schemas_absent():
    """Ensure no deprecated schema files are present."""
    for fname in DEPRECATED:
        path = CONTRACTS_DIR / fname
        assert not path.exists(), f"Deprecated schema file {fname} should have been removed"

def test_schema_validation():
    """Validate each sample instance against its schema."""
    for schema_name, sample in SCHEMAS.items():
        schema_path = CONTRACTS_DIR / schema_name
        assert schema_path.is_file(), f"Schema file {schema_name} missing"

        with schema_path.open("r", encoding="utf-8") as f:
            schema = yaml.safe_load(f)

        # jsonschema.validate will raise if invalid
        jsonschema.validate(instance=sample, schema=schema)
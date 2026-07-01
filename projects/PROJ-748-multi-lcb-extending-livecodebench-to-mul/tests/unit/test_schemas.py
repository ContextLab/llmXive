"""
Unit tests for JSON schemas.
Verifies that the schema definitions are valid YAML and can be loaded.
"""
import json
import tempfile
from pathlib import Path

import pytest
import yaml

from config import get_contracts_path


def load_schema(schema_name: str) -> dict:
    """Helper to load a schema by name."""
    contracts_dir = get_contracts_path()
    schema_path = contracts_dir / f"{schema_name}.schema.yaml"
    assert schema_path.exists(), f"Schema file not found: {schema_path}"
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture
def valid_dataset_payload():
    return {
        "meta": {
            "source": "livecodebench",
            "version": "1.0.0",
            "commit_hash": "abc123",
            "checksum": "sha256:...",
            "total_tasks": 100,
            "generated_at": "2024-01-01T00:00:00Z",
            "languages": ["python", "cpp"],
            "contamination_excluded_count": 5
        },
        "tasks": [
            {
                "task_id": "task_001",
                "question": "Add two numbers.",
                "difficulty": "easy",
                "language": "python",
                "test_cases": [
                    {
                        "input": "1 2",
                        "output": "3",
                        "timeout_ms": 1000
                    }
                ],
                "metadata": {
                    "release_date": "2023-01-01",
                    "original_id": "lc_001",
                    "contest_name": "TestContest",
                    "topic_tags": ["math"]
                }
            }
        ]
    }


@pytest.fixture
def valid_execution_log_payload():
    return {
        "meta": {
            "pipeline_version": "1.0.0",
            "start_time": "2024-01-01T00:00:00Z",
            "end_time": "2024-01-01T01:00:00Z",
            "config_snapshot": {
                "models": ["model_a"],
                "temperatures": [0.2],
                "seed": 42,
                "languages": ["python"]
            }
        },
        "run_results": [
            {
                "task_id": "task_001",
                "model": "model_a",
                "temperature": 0.2,
                "language": "python",
                "run_index": 0,
                "status": "pass",
                "timestamp": "2024-01-01T00:05:00Z",
                "duration_ms": 150,
                "tokens_used": {"prompt": 100, "completion": 50, "total": 150}
            }
        ],
        "aggregated_results": [
            {
                "model": "model_a",
                "language": "python",
                "temperature": 0.2,
                "pass_1": 1.0,
                "pass_5": 1.0,
                "pass_10": 1.0,
                "std_dev_pass_1": 0.0,
                "std_dev_pass_5": 0.0,
                "std_dev_pass_10": 0.0
            }
        ]
    }


@pytest.fixture
def valid_statistical_results_payload():
    return {
        "meta": {
            "analysis_timestamp": "2024-01-01T02:00:00Z",
            "input_log_path": "results/artifacts/execution_log.json",
            "methods_used": ["LOO-PCA", "GLMM"]
        },
        "correlation_analysis": {
            "python_pass1_vs_pc1": {
                "pearson_r": 0.85,
                "p_value": 0.001,
                "sample_size": 100
            },
            "intra_model_baseline": {
                "mean_correlation": 0.75,
                "std_correlation": 0.1
            }
        },
        "ranking_analysis": {
            "glmm_rankings": [
                {
                    "model": "model_a",
                    "rank": 1,
                    "estimated_effect": 0.9,
                    "confidence_interval": {"lower": 0.8, "upper": 1.0}
                }
            ],
            "significant_differences": [
                {
                    "model_a": "model_a",
                    "model_b": "model_b",
                    "p_value_raw": 0.001,
                    "p_value_corrected": 0.01,
                    "significant": True
                }
            ]
        }
    }


def test_schema_syntax():
    """Ensure all schema files are valid YAML."""
    for name in ["dataset", "execution_log", "statistical_results"]:
        schema = load_schema(name)
        assert isinstance(schema, dict), f"Schema {name} is not a dict"
        assert "$schema" in schema, f"Schema {name} missing $schema"


def test_dataset_schema_structure():
    """Ensure dataset schema has required top-level keys."""
    schema = load_schema("dataset")
    assert "properties" in schema
    assert "meta" in schema["properties"]
    assert "tasks" in schema["properties"]


def test_execution_log_schema_structure():
    """Ensure execution log schema has required top-level keys."""
    schema = load_schema("execution_log")
    assert "properties" in schema
    assert "meta" in schema["properties"]
    assert "run_results" in schema["properties"]


def test_statistical_results_schema_structure():
    """Ensure statistical results schema has required top-level keys."""
    schema = load_schema("statistical_results")
    assert "properties" in schema
    assert "meta" in schema["properties"]
    assert "correlation_analysis" in schema["properties"]
    assert "ranking_analysis" in schema["properties"]


def test_validate_dataset_payload(valid_dataset_payload):
    """Test that a valid dataset payload matches the schema."""
    try:
        import jsonschema
        schema = load_schema("dataset")
        jsonschema.validate(instance=valid_dataset_payload, schema=schema)
    except ImportError:
        pytest.skip("jsonschema not installed")
    except jsonschema.exceptions.ValidationError as e:
        pytest.fail(f"Valid dataset payload failed schema validation: {e}")


def test_validate_execution_log_payload(valid_execution_log_payload):
    """Test that a valid execution log payload matches the schema."""
    try:
        import jsonschema
        schema = load_schema("execution_log")
        jsonschema.validate(instance=valid_execution_log_payload, schema=schema)
    except ImportError:
        pytest.skip("jsonschema not installed")
    except jsonschema.exceptions.ValidationError as e:
        pytest.fail(f"Valid execution log payload failed schema validation: {e}")


def test_validate_statistical_results_payload(valid_statistical_results_payload):
    """Test that a valid statistical results payload matches the schema."""
    try:
        import jsonschema
        schema = load_schema("statistical_results")
        jsonschema.validate(instance=valid_statistical_results_payload, schema=schema)
    except ImportError:
        pytest.skip("jsonschema not installed")
    except jsonschema.exceptions.ValidationError as e:
        pytest.fail(f"Valid statistical results payload failed schema validation: {e}")

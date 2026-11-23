import pytest
import json
from pathlib import Path
from utils.data_utils import load_schema, validate_against_schema

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent.parent
contracts_dir = project_root / "specs" / "001-gene-regulation" / "contracts"

def get_schema_path() -> Path:
    return contracts_dir / "metrics_report.schema.yaml"

def load_sample_metrics_report() -> dict:
    """Load a sample metrics report structure for validation."""
    return {
        "model_accuracy": 0.85,
        "baseline_accuracy": 0.80,
        "improvement": 0.05,
        "mcnemar_p_value": 0.03,
        "confusion_matrix": {
            "true_positive": 100,
            "true_negative": 200,
            "false_positive": 50,
            "false_negative": 50
        },
        "sensitivity_analysis": {
            "variance": 0.02
        },
        "associational_framing": True
    }

def test_metrics_report_schema_exists():
    """Verify that the metrics report schema file exists."""
    schema_path = get_schema_path()
    assert schema_path.exists(), f"Metrics report schema not found at {schema_path}"

def test_metrics_report_schema_loads():
    """Verify that the metrics report schema can be loaded."""
    schema_path = get_schema_path()
    schema = load_schema(str(schema_path))
    assert schema is not None
    assert "type" in schema or "properties" in schema

def test_sample_metrics_report_conforms():
    """Verify that a sample metrics report conforms to the schema."""
    schema_path = get_schema_path()
    schema = load_schema(str(schema_path))
    sample_data = load_sample_metrics_report()
    try:
        validate_against_schema(sample_data, schema)
    except Exception as e:
        pytest.fail(f"Sample metrics report failed schema validation: {e}")

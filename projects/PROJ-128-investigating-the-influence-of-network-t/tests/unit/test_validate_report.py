import os
import json
import tempfile
import pytest
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from reports.validate_report import (
    load_schema,
    validate_field_presence,
    validate_report_structure,
    validate_report_file
)

def test_validate_missing_required_field():
    """Test that missing required fields are detected."""
    schema = {
        "type": "object",
        "required": ["field_a", "field_b"],
        "properties": {
            "field_a": {"type": "string"},
            "field_b": {"type": "number"}
        }
    }
    data = {"field_a": "test"}
    
    errors = validate_field_presence(data, schema)
    
    assert len(errors) == 1
    assert "Missing required field: field_b" in errors[0]

def test_validate_nested_missing_field():
    """Test detection of missing fields in nested objects."""
    schema = {
        "type": "object",
        "required": ["parent"],
        "properties": {
            "parent": {
                "type": "object",
                "required": ["child"],
                "properties": {
                    "child": {"type": "string"}
                }
            }
        }
    }
    data = {"parent": {}}
    
    errors = validate_field_presence(data, schema)
    
    assert len(errors) == 1
    assert "Missing required field: parent.child" in errors[0]

def test_validate_array_items():
    """Test validation of items within an array."""
    schema = {
        "type": "object",
        "required": ["items"],
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id"],
                    "properties": {
                        "id": {"type": "integer"}
                    }
                }
            }
        }
    }
    data = {"items": [{"id": 1}, {}]}
    
    errors = validate_field_presence(data, schema)
    
    assert len(errors) == 1
    assert "Missing required field: items[1].id" in errors[0]

def test_validate_full_report_schema():
    """Test validation against the full output schema."""
    schema_path = Path("contracts/output.schema.yaml")
    if not schema_path.exists():
        pytest.skip("Schema file not found, skipping full schema test")
    
    schema = load_schema(str(schema_path))
    
    # Create a minimal valid report
    valid_report = {
        "metadata": {
            "pipeline_version": "1.0",
            "generation_timestamp": "2023-01-01T00:00:00",
            "data_source": "HCP",
            "total_subjects_processed": 10,
            "total_subjects_excluded": 0
        },
        "structural_metrics_summary": {
            "global_efficiency": {"mean": 0.5, "std": 0.1, "min": 0.3, "max": 0.7},
            "clustering_coefficient": {"mean": 0.4, "std": 0.1, "min": 0.2, "max": 0.6},
            "modularity": {"mean": 0.6, "std": 0.1, "min": 0.4, "max": 0.8}
        },
        "dynamic_metrics_summary": {
            "mean_dwell_time": {"mean": 10.0, "std": 2.0, "min": 5.0, "max": 15.0},
            "visited_states_count": {"mean": 5.0, "std": 1.0, "min": 3.0, "max": 7.0}
        },
        "correlation_analysis": {
            "pairs": [
                {"metric_a": "eff", "metric_b": "dwell", "r_value": 0.5, "p_value": 0.01, "method": "pearson"}
            ],
            "fdr_corrected_pairs": [
                {"metric_a": "eff", "metric_b": "dwell", "p_value_raw": 0.01, "p_value_fdr": 0.02, "is_significant": True}
            ],
            "summary_statement": "Significant correlation found."
        },
        "sensitivity_analysis": {
            "window_length_sensitivity": {
                "baseline_window_tr": 30,
                "sensitivity_window_tr": 20,
                "absolute_difference_correlation": 0.05
            },
            "density_threshold_sensitivity": {
                "baseline_threshold": 0.1,
                "variations": []
            }
        },
        "exclusions": {
            "count": 0,
            "reasons": {
                "convergence_failure": 0,
                "sparsity_exclusion": 0,
                "other": 0
            }
        }
    }
    
    is_valid, errors = validate_report_structure(valid_report, schema)
    assert is_valid, f"Valid report failed validation: {errors}"

def test_validate_report_file_missing_file():
    """Test validation when report file is missing."""
    is_valid, errors = validate_report_file("nonexistent.json", "contracts/output.schema.yaml")
    assert not is_valid
    assert len(errors) == 1
    assert "not found" in errors[0].lower()
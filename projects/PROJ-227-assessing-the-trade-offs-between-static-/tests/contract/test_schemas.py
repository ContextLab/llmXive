import pytest
import yaml
import json
import jsonschema
from pathlib import Path

# Helper to load schema
def load_schema(name):
    schema_path = Path(__file__).parent.parent.parent / "contracts" / name
    with open(schema_path, 'r') as f:
        if name.endswith('.yaml'):
            return yaml.safe_load(f)
        return json.load(f)

# Helper to create minimal valid instance
def get_minimal_instance(schema_name):
    schema = load_schema(schema_name)
    instance = {}
    
    # Hardcoded minimal valid data for each schema to ensure robust testing
    if schema_name == "dataset.schema.yaml":
        instance = {
            "metadata": {
                "source": "humaneval",
                "language": "python",
                "version": "1.0",
                "timestamp": "2023-01-01T00:00:00Z",
                "record_count": 1
            },
            "records": [
                {"id": "test-1", "prompt": "def foo(): pass"}
            ]
        }
    elif schema_name == "analysis_log.schema.yaml":
        instance = {
            "tool_name": "codeql",
            "version": "1.0",
            "timestamp": "2023-01-01T00:00:00Z",
            "status": "success",
            "results": []
        }
    elif schema_name == "analysis_results.schema.yaml":
        instance = {
            "snippet_id": "test-1",
            "language": "python",
            "static_results": {"tool": "codeql", "issue_count": 0, "issues": []},
            "dynamic_results": {"tool": "pytest", "total_tests": 1, "passed_tests": 1, "failed_tests": 0, "pass_rate": 1.0, "is_untestable": False},
            "correlation": {"static_issue_detected": False, "dynamic_test_failed": False, "match": True}
        }
    elif schema_name == "dataset_manifest.schema.yaml":
        instance = {
            "version": "1.0",
            "generated_at": "2023-01-01T00:00:00Z",
            "total_records": 1,
            "strata": {"python": 1},
            "records": [
                {
                    "id": "test-1",
                    "language": "python",
                    "source": "humaneval",
                    "stratum": "python",
                    "static_only": False,
                    "file_path": "data/raw/test.json"
                }
            ]
        }
    elif schema_name == "statistical_report.schema.yaml":
        instance = {
            "report_version": "1.0",
            "generated_at": "2023-01-01T00:00:00Z",
            "methodology": {
                "static_metric": "Issue Detection Rate",
                "dynamic_metric": "Pass Rate",
                "correlation_test": "Spearman"
            },
            "metrics": {"overall_issue_detection_rate": 0.5, "overall_pass_rate": 0.9, "sample_size": 100},
            "correlations": {
                "spearman": {"coefficient": 0.5, "p_value": 0.01, "significant": True},
                "chi_squared": {"statistic": 10.0, "p_value": 0.01, "degrees_of_freedom": 1, "significant": True}
            },
            "stratified_results": {"python": {"sample_size": 100, "issue_detection_rate": 0.5, "pass_rate": 0.9}},
            "sensitivity_analysis": {
                "alpha_levels": [0.01, 0.05, 0.1],
                "results_by_alpha": {
                    "0.01": {"significant": True, "effect_size": 0.5}
                }
            }
        }
    elif schema_name == "tool_version.schema.yaml":
        instance = {
            "tools": [
                {"name": "codeql", "version": "2.0", "timestamp": "2023-01-01T00:00:00Z"}
            ]
        }
    else:
        raise ValueError(f"Unknown schema: {schema_name}")
    
    return instance

@pytest.mark.parametrize("schema_file", [
    "dataset.schema.yaml",
    "analysis_log.schema.yaml",
    "analysis_results.schema.yaml",
    "dataset_manifest.schema.yaml",
    "statistical_report.schema.yaml",
    "tool_version.schema.yaml"
])
def test_schema_validation(schema_file):
    """Verify that minimal valid samples pass JSON Schema validation."""
    schema = load_schema(schema_file)
    instance = get_minimal_instance(schema_file)
    
    try:
        jsonschema.validate(instance=instance, schema=schema)
    except jsonschema.exceptions.ValidationError as e:
        pytest.fail(f"Schema {schema_file} failed validation: {e.message}")
import pytest
import json
import yaml
import jsonschema
from pathlib import Path

# Helper to load schema
def load_schema(schema_path: str) -> dict:
    path = Path(schema_path)
    with open(path, 'r') as f:
        if path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        else:
            return json.load(f)

@pytest.fixture
def contracts_dir():
    return Path(__file__).parent.parent.parent / 'contracts'

def test_dataset_schema_valid(contracts_dir):
    schema = load_schema(contracts_dir / 'dataset.schema.yaml')
    valid_data = {
        "id": "humaneval-v1",
        "source": "openai/human-eval",
        "language": "python",
        "record_count": 164,
        "checksum": "abc123",
        "created_at": "2023-10-01T12:00:00Z",
        "static_only": False,
        "path": "data/raw/humaneval.json"
    }
    jsonschema.validate(instance=valid_data, schema=schema)

def test_analysis_log_schema_valid(contracts_dir):
    schema = load_schema(contracts_dir / 'analysis_log.schema.yaml')
    valid_data = {
        "id": "run-001",
        "language": "python",
        "tool": "CodeQL",
        "version": "2.14.0",
        "timestamp": "2023-10-01T12:00:00Z",
        "status": "success",
        "duration_seconds": 1.5,
        "issues": [
            {
                "severity": "medium",
                "rule_id": "PY-001",
                "message": "Unused variable",
                "location": "file.py:10"
            }
        ],
        "output_path": "data/processed/log_run_001.json"
    }
    jsonschema.validate(instance=valid_data, schema=schema)

def test_analysis_results_schema_valid(contracts_dir):
    schema = load_schema(contracts_dir / 'analysis_results.schema.yaml')
    valid_data = {
        "snippet_id": "snippet-123",
        "language": "python",
        "static_issues_count": 2,
        "static_severities": {
            "low": 0,
            "medium": 2,
            "high": 0,
            "critical": 0
        },
        "dynamic_pass": True,
        "dynamic_coverage": 85.5,
        "analysis_timestamp": "2023-10-01T12:05:00Z",
        "tools_used": ["CodeQL", "pytest"]
    }
    jsonschema.validate(instance=valid_data, schema=schema)

def test_dataset_manifest_schema_valid(contracts_dir):
    schema = load_schema(contracts_dir / 'dataset_manifest.schema.yaml')
    valid_data = {
        "version": "1.0",
        "created_at": "2023-10-01T12:00:00Z",
        "total_records": 500,
        "strata": {
            "python": {"count": 200, "static_only_count": 50, "dynamic_eligible_count": 150}
        },
        "records": [
            {
                "id": "sample-1",
                "language": "python",
                "source": "humaneval",
                "stratum": "python",
                "static_only": False,
                "path": "data/raw/sample-1.json"
            }
        ]
    }
    jsonschema.validate(instance=valid_data, schema=schema)

def test_statistical_report_schema_valid(contracts_dir):
    schema = load_schema(contracts_dir / 'statistical_report.schema.yaml')
    valid_data = {
        "report_id": "report-001",
        "generated_at": "2023-10-01T12:00:00Z",
        "methodology": "Spearman correlation and Chi-squared test",
        "metrics": {
            "issue_detection_rate": {"python": 0.15},
            "pass_rate": {"python": 0.85},
            "correlation": {
                "method": "Spearman",
                "coefficient": -0.45,
                "p_value": 0.001,
                "sample_size": 500
            },
            "chi_squared": {
                "statistic": 12.5,
                "p_value": 0.002,
                "degrees_of_freedom": 1
            }
        },
        "stratified_results": [
            {"stratum": "python", "results": {"rate": 0.15}}
        ],
        "sensitivity_analysis": {"alpha_0.05": "significant"},
        "corrections": {
            "method": "Bonferroni",
            "adjusted_p_values": [0.003]
        },
        "notes": "No major limitations found."
    }
    jsonschema.validate(instance=valid_data, schema=schema)

def test_tool_version_schema_valid(contracts_dir):
    schema = load_schema(contracts_dir / 'tool_version.schema.yaml')
    valid_data = {
        "tool_name": "CodeQL",
        "version": "2.14.0",
        "installation_date": "2023-09-01T10:00:00Z",
        "path": "/usr/local/bin/codeql",
        "environment": {"PATH": "/usr/local/bin"},
        "checksum": "sha256:abc123..."
    }
    jsonschema.validate(instance=valid_data, schema=schema)
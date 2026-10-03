"""
Unit tests for JSON Schema validation of project artifacts.
Tests T005: Verify schemas are valid and can validate sample data.
"""
import json
import yaml
import pytest
import jsonschema
from pathlib import Path

# Base path for contracts
CONTRACTS_DIR = Path(__file__).parent.parent.parent / "contracts"

# Sample data generators
def get_sample_dataset():
    return {
        "dataset_id": "humaneval-test",
        "language": "python",
        "source_url": "https://huggingface.co/datasets/openai/human-eval",
        "download_timestamp": "2023-10-01T12:00:00Z",
        "record_count": 164,
        "checksum": "a" * 64,
        "samples": [
            {
                "task_id": "HumanEval/0",
                "code": "def add(a, b):\n    return a + b",
                "prompt": "Write a function to add two numbers",
                "test": "assert add(1, 2) == 3"
            }
        ]
    }

def get_sample_analysis_log():
    return {
        "analysis_id": "analysis-001",
        "dataset_id": "humaneval-test",
        "language": "python",
        "tool": "codeql",
        "tool_version": "2.14.0",
        "timestamp": "2023-10-01T12:30:00Z",
        "execution_time_ms": 1500,
        "results": [
            {
                "snippet_id": "HumanEval/0",
                "status": "passed",
                "issues": [
                    {
                        "severity": "warning",
                        "rule_id": "CWE-798",
                        "message": "Hardcoded credentials detected",
                        "location": {"line": 1, "column": 0}
                    }
                ]
            }
        ]
    }

def get_sample_analysis_results():
    return {
        "snippet_id": "HumanEval/0",
        "dataset_id": "humaneval-test",
        "language": "python",
        "static_analysis": {
            "tool": "codeql",
            "issue_count": 1,
            "issues": [
                {"severity": "warning", "rule_id": "CWE-798", "message": "Hardcoded credentials"}
            ],
            "fallback_used": False
        },
        "dynamic_analysis": {
            "status": "passed",
            "pass_rate": 1.0,
            "test_count": 1,
            "duration_ms": 200
        },
        "correlation_metadata": {
            "static_issue_density": 0.5,
            "dynamic_complexity": 1.2
        }
    }

def get_sample_manifest():
    return {
        "manifest_version": "1.0",
        "created_at": "2023-10-01T12:00:00Z",
        "datasets": [
            {
                "dataset_id": "humaneval-test",
                "file_path": "data/raw/humaneval.json",
                "record_count": 164,
                "language": "python",
                "static_only": False,
                "checksum": "b" * 64
            }
        ],
        "summary": {
            "total_records": 164,
            "total_datasets": 1,
            "language_breakdown": {"python": 164, "javascript": 0, "java": 0},
            "static_only_count": 0,
            "dynamic_capable_count": 164
        },
        "validation_status": {
            "passed": True,
            "errors": [],
            "warnings": []
        }
    }

def get_sample_statistical_report():
    return {
        "report_id": "report-001",
        "generated_at": "2023-10-01T13:00:00Z",
        "methodology": {
            "primary_metric_static": "issue_detection_rate",
            "primary_metric_dynamic": "pass_rate",
            "correlation_method": "spearman",
            "significance_level": 0.05,
            "bonferroni_corrected": True,
            "deviations": ["FR-004", "FR-005", "SC-002"]
        },
        "metrics": {
            "issue_detection_rate": {"overall": 0.45, "by_language": {"python": 0.45, "javascript": 0.0, "java": 0.0}},
            "pass_rate": {"overall": 0.72, "by_language": {"python": 0.72, "javascript": 0.0, "java": 0.0}}
        },
        "correlation_results": {
            "spearman": {"coefficient": -0.12, "p_value": 0.23, "sample_size": 164},
            "chi_squared": {"statistic": 2.1, "p_value": 0.15, "degrees_of_freedom": 1}
        },
        "stratified_results": [
            {"language": "python", "sample_size": 164, "metrics": {}}
        ],
        "sensitivity_analysis": [
            {"alpha": 0.01, "detection_rate": 0.45, "p_value": 0.23, "sample_size": 164},
            {"alpha": 0.05, "detection_rate": 0.45, "p_value": 0.23, "sample_size": 164},
            {"alpha": 0.1, "detection_rate": 0.45, "p_value": 0.23, "sample_size": 164}
        ],
        "limitations": ["Sample size limited for JS/Java"],
        "artifacts": {
            "raw_data_hash": "c" * 64,
            "processed_data_hash": "d" * 64,
            "tool_versions": {"codeql": "2.14.0"}
        }
    }

def get_sample_tool_version():
    return {
        "recorded_at": "2023-10-01T11:00:00Z",
        "tools": [
            {
                "name": "codeql",
                "version": "2.14.0",
                "path_or_id": "/usr/local/bin/codeql",
                "platform": "linux",
                "install_method": "cli",
                "notes": "Official release"
            },
            {
                "name": "pytest",
                "version": "7.4.0",
                "path_or_id": "pytest==7.4.0",
                "platform": "linux",
                "install_method": "pip"
            }
        ],
        "verification_status": {
            "all_verified": True,
            "failed_verifications": []
        }
    }

SAMPLE_DATA = {
    "dataset.schema.yaml": get_sample_dataset,
    "analysis_log.schema.yaml": get_sample_analysis_log,
    "analysis_results.schema.yaml": get_sample_analysis_results,
    "dataset_manifest.schema.yaml": get_sample_manifest,
    "statistical_report.schema.yaml": get_sample_statistical_report,
    "tool_version.schema.yaml": get_sample_tool_version
}

@pytest.mark.parametrize("schema_file", SAMPLE_DATA.keys())
def test_schema_syntax(schema_file):
    """Verify each schema file is valid YAML and JSON Schema."""
    schema_path = CONTRACTS_DIR / schema_file
    assert schema_path.exists(), f"Schema file missing: {schema_path}"

    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)

    # Basic JSON Schema structure check
    assert "$schema" in schema or "title" in schema, "Invalid JSON Schema structure"

@pytest.mark.parametrize("schema_file, sample_func", SAMPLE_DATA.items())
def test_schema_validation(schema_file, sample_func):
    """Verify each schema can successfully validate its sample data."""
    schema_path = CONTRACTS_DIR / schema_file
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)

    sample_data = sample_func()

    # This will raise jsonschema.ValidationError if invalid
    try:
        jsonschema.validate(instance=sample_data, schema=schema)
    except jsonschema.ValidationError as e:
        pytest.fail(f"Validation failed for {schema_file}: {e.message}")

def test_all_schemas_exist():
    """Verify all required schema files exist."""
    required_schemas = [
        "dataset.schema.yaml",
        "analysis_log.schema.yaml",
        "analysis_results.schema.yaml",
        "dataset_manifest.schema.yaml",
        "statistical_report.schema.yaml",
        "tool_version.schema.yaml"
    ]
    for schema_name in required_schemas:
        schema_path = CONTRACTS_DIR / schema_name
        assert schema_path.exists(), f"Missing required schema: {schema_path}"

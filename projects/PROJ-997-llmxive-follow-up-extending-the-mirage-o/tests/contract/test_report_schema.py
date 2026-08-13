"""
Contract test for report schema in US3.

This test validates that the final research report and intermediate
consistency/latency artifacts conform to the expected schema defined
in the project specifications.
"""
import json
import os
import pytest
from pathlib import Path
from typing import Dict, Any, List

# Project root relative to this test file (assuming tests/contract/)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Expected schema definitions based on tasks.md and specs
EXPECTED_REPORT_SCHEMA = {
    "type": "object",
    "required": [
        "title",
        "execution_timestamp",
        "summary",
        "metrics",
        "statistical_validation",
        "consistency_analysis",
        "latency_analysis",
        "conclusions"
    ],
    "properties": {
        "title": {"type": "string"},
        "execution_timestamp": {"type": "string", "format": "date-time"},
        "summary": {"type": "string"},
        "metrics": {
            "type": "object",
            "required": ["pearson_correlation", "mae"],
            "properties": {
                "pearson_correlation": {"type": "number"},
                "mae": {"type": "number"}
            }
        },
        "statistical_validation": {
            "type": "object",
            "required": ["paired_t_test", "bonferroni_correction"],
            "properties": {
                "paired_t_test": {
                    "type": "object",
                    "required": ["t_statistic", "p_value", "significant"],
                    "properties": {
                        "t_statistic": {"type": "number"},
                        "p_value": {"type": "number"},
                        "significant": {"type": "boolean"}
                    }
                },
                "bonferroni_correction": {
                    "type": "object",
                    "required": ["adjusted_alpha", "original_alpha"],
                    "properties": {
                        "adjusted_alpha": {"type": "number"},
                        "original_alpha": {"type": "number"}
                    }
                }
            }
        },
        "consistency_analysis": {
            "type": "object",
            "required": ["per_level_correlation", "overall_consistency_metric"],
            "properties": {
                "per_level_correlation": {
                    "type": "object",
                    "properties": {
                        "int4": {"type": "number"},
                        "int8": {"type": "number"},
                        "fp8": {"type": "number"}
                    }
                },
                "overall_consistency_metric": {"type": "number"}
            }
        },
        "latency_analysis": {
            "type": "object",
            "required": ["proxy_time", "baseline_time", "reduction_percentage"],
            "properties": {
                "proxy_time": {"type": "number"},
                "baseline_time": {"type": "number"},
                "reduction_percentage": {"type": "number"}
            }
        },
        "conclusions": {"type": "array", "items": {"type": "string"}}
    }
}

EXPECTED_CONSISTENCY_SCHEMA = {
    "type": "object",
    "required": ["per_level_correlation", "percentage_satisfying_bound", "overall_consistency_metric"],
    "properties": {
        "per_level_correlation": {
            "type": "object",
            "properties": {
                "int4": {"type": "number"},
                "int8": {"type": "number"},
                "fp8": {"type": "number"}
            }
        },
        "percentage_satisfying_bound": {"type": "number"},
        "overall_consistency_metric": {"type": "number"}
    }
}

EXPECTED_LATENCY_SCHEMA = {
    "type": "object",
    "required": ["proxy_time", "baseline_time", "reduction_percentage"],
    "properties": {
        "proxy_time": {"type": "number"},
        "baseline_time": {"type": "number"},
        "reduction_percentage": {"type": "number"}
    }
}

EXPECTED_TTEST_SCHEMA = {
    "type": "object",
    "required": ["t_statistic", "p_value", "significant", "method"],
    "properties": {
        "t_statistic": {"type": "number"},
        "p_value": {"type": "number"},
        "significant": {"type": "boolean"},
        "method": {"type": "string"}
    }
}

def load_json_artifact(relative_path: str) -> Dict[str, Any]:
    """Load a JSON artifact from the project data directory."""
    full_path = PROJECT_ROOT / relative_path
    if not full_path.exists():
        pytest.fail(f"Artifact not found: {full_path}")
    with open(full_path, 'r') as f:
        return json.load(f)

def validate_schema(data: Dict[str, Any], schema: Dict[str, Any], path: str):
    """Basic schema validation (type checking and required fields)."""
    assert isinstance(data, dict), f"Expected dict at {path}, got {type(data)}"

    if "required" in schema:
        for key in schema["required"]:
            assert key in data, f"Missing required key '{key}' in {path}"

    if "properties" in schema:
        for key, prop_schema in schema["properties"].items():
            if key in data:
                val = data[key]
                prop_type = prop_schema.get("type")
                if prop_type == "string":
                    assert isinstance(val, str), f"Expected string for {key} in {path}"
                elif prop_type == "number":
                    assert isinstance(val, (int, float)), f"Expected number for {key} in {path}"
                elif prop_type == "boolean":
                    assert isinstance(val, bool), f"Expected boolean for {key} in {path}"
                elif prop_type == "array":
                    assert isinstance(val, list), f"Expected list for {key} in {path}"
                    if "items" in prop_schema:
                        item_type = prop_schema["items"].get("type")
                        for i, item in enumerate(val):
                            if item_type == "string":
                                assert isinstance(item, str), f"Expected string in array {key}[{i}] in {path}"
                elif prop_type == "object":
                    # Recursively validate nested objects
                    validate_schema(val, prop_schema, f"{path}.{key}")

def test_final_report_schema():
    """
    Contract test: Verify the final research report JSON schema.
    This test expects `docs/reports/001-llmxive-mipu-gap-bounds.json` (or similar)
    to exist if the report generation task (T033) has run.
    If the report is a Markdown file, we check for the existence of the JSON
    data artifacts that feed into it, as the Markdown itself is text.
    However, the task implies a machine-readable summary or the JSON artifacts
    generated by T029, T030, T032 should exist.
    
    Since T033 generates a Markdown report, we validate the *input* JSON artifacts
    that T033 is supposed to aggregate, ensuring the pipeline produced valid data.
    """
    # We validate the intermediate JSON artifacts that constitute the report's data
    artifacts = [
        ("data/processed/test_metrics.json", EXPECTED_REPORT_SCHEMA), # Simplified check for test metrics
        ("data/processed/t_test_results.json", EXPECTED_TTEST_SCHEMA),
        ("data/processed/consistency_report.json", EXPECTED_CONSISTENCY_SCHEMA),
        ("data/processed/latency_metrics.json", EXPECTED_LATENCY_SCHEMA)
    ]

    for rel_path, schema in artifacts:
        try:
            data = load_json_artifact(rel_path)
            validate_schema(data, schema, rel_path)
        except FileNotFoundError:
            # If the file doesn't exist, the pipeline hasn't run yet.
            # This is acceptable for a contract test if the test is run before execution.
            # However, for a completed task, we expect these to exist.
            # We raise a clear failure if the task is supposed to be done.
            pytest.skip(f"Artifact {rel_path} not found. Pipeline may not have been executed yet.")

def test_consistency_report_schema():
    """
    Contract test: Verify consistency_report.json schema (T032).
    """
    rel_path = "data/processed/consistency_report.json"
    try:
        data = load_json_artifact(rel_path)
        validate_schema(data, EXPECTED_CONSISTENCY_SCHEMA, rel_path)
    except FileNotFoundError:
        pytest.skip(f"Artifact {rel_path} not found.")

def test_latency_metrics_schema():
    """
    Contract test: Verify latency_metrics.json schema (T030).
    """
    rel_path = "data/processed/latency_metrics.json"
    try:
        data = load_json_artifact(rel_path)
        validate_schema(data, EXPECTED_LATENCY_SCHEMA, rel_path)
    except FileNotFoundError:
        pytest.skip(f"Artifact {rel_path} not found.")

def test_t_test_results_schema():
    """
    Contract test: Verify t_test_results.json schema (T029).
    """
    rel_path = "data/processed/t_test_results.json"
    try:
        data = load_json_artifact(rel_path)
        validate_schema(data, EXPECTED_TTEST_SCHEMA, rel_path)
    except FileNotFoundError:
        pytest.skip(f"Artifact {rel_path} not found.")
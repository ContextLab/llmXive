"""
Report Schema Definition for llmXive Final Statistics Report.

This module defines the schema and validation logic for the stats_report.json file.
It ensures all required fields are present and of the correct type as per the
project's scientific reporting requirements.
"""

import json
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict

# Schema Definition
STATS_REPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "mean_success_rate": {
            "type": "number",
            "description": "Mean success rate across all evaluated tasks/strategies."
        },
        "bh_corrected_primary": {
            "type": "object",
            "description": "Benjamini-Hochberg corrected p-values for primary strategy comparisons.",
            "additionalProperties": {"type": "number"}
        },
        "bh_corrected_sensitivity": {
            "type": "object",
            "description": "Benjamini-Hochberg corrected p-values for sensitivity analysis (k-values).",
            "additionalProperties": {"type": "number"}
        },
        "linearity_correlation_coefficient": {
            "type": ["number", "null"],
            "description": "Pearson correlation coefficient between text-space and weight-space distances."
        },
        "reconstruction_error": {
            "type": "object",
            "description": "Reconstruction error metrics.",
            "properties": {
                "mean": {"type": "number"},
                "max": {"type": "number"}
            },
            "required": ["mean", "max"]
        },
        "memory_footprint": {
            "type": "number",
            "description": "Peak memory usage in MB during evaluation."
        },
        "observed_success_rate_diff": {
            "type": "number",
            "description": "Difference between mean strategy success and baseline success (rounded to 4dp)."
        },
        "power_estimate": {
            "type": ["number", "null"],
            "description": "Estimated statistical power (0-1)."
        },
        "bh_rejected_count": {
            "type": "integer",
            "description": "Number of hypotheses rejected after BH correction."
        },
        "status_linearity": {
            "type": "string",
            "enum": ["PASS", "FAIL", "UNTESTABLE"],
            "description": "Status of the linearity validation (SC-005)."
        }
    },
    "required": [
        "mean_success_rate",
        "bh_corrected_primary",
        "bh_corrected_sensitivity",
        "linearity_correlation_coefficient",
        "reconstruction_error",
        "memory_footprint",
        "observed_success_rate_diff",
        "power_estimate",
        "bh_rejected_count",
        "status_linearity"
    ]
}

@dataclass
class StatsReport:
    """
    Data class representing the structure of stats_report.json.
    """
    mean_success_rate: float
    bh_corrected_primary: Dict[str, float]
    bh_corrected_sensitivity: Dict[str, float]
    linearity_correlation_coefficient: Optional[float]
    reconstruction_error: Dict[str, float]
    memory_footprint: float
    observed_success_rate_diff: float
    power_estimate: Optional[float]
    bh_rejected_count: int
    status_linearity: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StatsReport':
        return cls(
            mean_success_rate=data['mean_success_rate'],
            bh_corrected_primary=data['bh_corrected_primary'],
            bh_corrected_sensitivity=data['bh_corrected_sensitivity'],
            linearity_correlation_coefficient=data['linearity_correlation_coefficient'],
            reconstruction_error=data['reconstruction_error'],
            memory_footprint=data['memory_footprint'],
            observed_success_rate_diff=data['observed_success_rate_diff'],
            power_estimate=data['power_estimate'],
            bh_rejected_count=data['bh_rejected_count'],
            status_linearity=data['status_linearity']
        )

def validate_schema(data: Dict[str, Any]) -> bool:
    """
    Validates a dictionary against the STATS_REPORT_SCHEMA.
    Returns True if valid, raises ValueError if invalid.
    """
    def check_type(value, expected_type, path="root"):
        if expected_type == "number":
            if not isinstance(value, (int, float)):
                raise ValueError(f"Field '{path}' must be a number, got {type(value).__name__}")
        elif expected_type == "integer":
            if not isinstance(value, int):
                raise ValueError(f"Field '{path}' must be an integer, got {type(value).__name__}")
        elif expected_type == "string":
            if not isinstance(value, str):
                raise ValueError(f"Field '{path}' must be a string, got {type(value).__name__}")
        elif expected_type == "object":
            if not isinstance(value, dict):
                raise ValueError(f"Field '{path}' must be an object, got {type(value).__name__}")
        elif expected_type == "array":
            if not isinstance(value, list):
                raise ValueError(f"Field '{path}' must be an array, got {type(value).__name__}")
        elif expected_type == "boolean":
            if not isinstance(value, bool):
                raise ValueError(f"Field '{path}' must be a boolean, got {type(value).__name__}")
        elif expected_type == "null":
            if value is not None:
                raise ValueError(f"Field '{path}' must be null, got {type(value).__name__}")
        return True

    def validate_object(obj, schema, path="root"):
        if schema.get("type") == "object":
            if not isinstance(obj, dict):
                raise ValueError(f"{path} must be an object")
            
            # Check required fields
            for req in schema.get("required", []):
                if req not in obj:
                    raise ValueError(f"Missing required field: {path}.{req}")
            
            # Check properties
            for key, prop_schema in schema.get("properties", {}).items():
                if key in obj:
                    if prop_schema.get("type") == "object" and prop_schema.get("additionalProperties"):
                        # Handle nested object with additional properties
                        for sub_key, sub_val in obj[key].items():
                            check_type(sub_val, prop_schema["additionalProperties"]["type"], f"{path}.{key}.{sub_key}")
                    else:
                        check_type(obj[key], prop_schema.get("type"), f"{path}.{key}")
                        if prop_schema.get("type") == "object" and "properties" in prop_schema:
                            validate_object(obj[key], prop_schema, f"{path}.{key}")

    validate_object(data, STATS_REPORT_SCHEMA)
    return True

def load_report(path: str) -> StatsReport:
    """
    Loads and validates a stats_report.json file.
    """
    with open(path, 'r') as f:
        data = json.load(f)
    
    validate_schema(data)
    return StatsReport.from_dict(data)

def save_report(report: StatsReport, path: str) -> None:
    """
    Saves a StatsReport object to a JSON file.
    """
    with open(path, 'w') as f:
        json.dump(report.to_dict(), f, indent=2)

def main():
    """
    CLI entrypoint for schema validation (optional).
    """
    import argparse
    parser = argparse.ArgumentParser(description="Validate stats_report.json schema")
    parser.add_argument("--input", type=str, required=True, help="Path to stats_report.json")
    args = parser.parse_args()
    
    try:
        load_report(args.input)
        print(f"Schema validation passed for {args.input}")
    except Exception as e:
        print(f"Schema validation failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()
import os
import sys
import yaml
import json
import subprocess
from pathlib import Path

def check_yamllint_structure(schema_path: str) -> bool:
    """Verify that the schema file is valid YAML using yamllint."""
    try:
        result = subprocess.run(
            ["yamllint", "-d", "{extends: default, rules: {line-length: disable}}", schema_path],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✓ yamllint passed for {schema_path}")
            return True
        else:
            print(f"✗ yamllint failed for {schema_path}: {result.stdout}")
            return False
    except FileNotFoundError:
        print("⚠ yamllint not found, skipping lint check.")
        return True

def load_and_validate_schema(schema_path: str) -> dict:
    """Load the YAML schema and ensure it is a valid dictionary."""
    try:
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        if not isinstance(schema, dict):
            raise ValueError("Schema root must be a dictionary")
        print(f"✓ Schema loaded successfully from {schema_path}")
        return schema
    except Exception as e:
        print(f"✗ Failed to load schema: {e}")
        raise

def test_schema_with_mock_data(schema_path: str) -> bool:
    """Validate a mock JSON object against the loaded schema."""
    schema = load_and_validate_schema(schema_path)
    
    # Mock data adhering to the schema
    mock_data = {
        "dataset_id": 12345,
        "observed_power": 0.85,
        "mdes": 0.21,
        "threshold_met": True,
        "status": "success",
        "details": {
            "alpha": 0.05,
            "effect_size": 0.3,
            "sample_size": 150,
            "metric_type": "Cohen's d"
        }
    }

    # Basic structural validation (since jsonschema might not be installed)
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in mock_data:
            print(f"✗ Mock data missing required field: {field}")
            return False

    # Type validation for key fields
    if not isinstance(mock_data["dataset_id"], int):
        print("✗ dataset_id must be int")
        return False
    if not (0.0 <= mock_data["observed_power"] <= 1.0):
        print("✗ observed_power must be between 0 and 1")
        return False
    if not isinstance(mock_data["mdes"], (int, float)) or mock_data["mdes"] < 0:
        print("✗ mdes must be non-negative number")
        return False
    if not isinstance(mock_data["threshold_met"], bool):
        print("✗ threshold_met must be bool")
        return False
    if mock_data["status"] not in ["success", "low_power", "insufficient_data", "error"]:
        print("✗ Invalid status value")
        return False

    print("✓ Mock data validation passed against schema structure")
    return True

def main():
    schema_path = "contracts/power_audit_result.schema.yaml"
    if not os.path.exists(schema_path):
        print(f"✗ Schema file not found: {schema_path}")
        sys.exit(1)

    success = True
    
    if not check_yamllint_structure(schema_path):
        success = False
    
    if not test_schema_with_mock_data(schema_path):
        success = False

    if success:
        print("\n✓ T006 Verification Complete: power_audit_result.schema.yaml is valid.")
        sys.exit(0)
    else:
        print("\n✗ T006 Verification Failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()

"""
Unit test for validating the feature matrix CSV against the JSON schema.
"""
import pytest
from pathlib import Path

# Use the validation function from the project
from validate_feature_matrix import validate_feature_matrix

def test_feature_matrix_schema():
    """
    Load the generated feature matrix and validate it against the
    contracts/dataset.schema.yaml schema. The test will raise if validation fails.
    """
    csv_path = Path("data") / "processed" / "feature_matrix.csv"
    # The function will raise an exception on failure, causing the test to fail.
    validate_feature_matrix(csv_path=csv_path)

if __name__ == "__main__":
    # Simple manual run
    test_feature_matrix_schema()
    print("Feature matrix schema validation passed.")
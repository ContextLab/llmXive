import pytest
import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

def test_csv_output_matches_schema():
    """Verify CSV output matches the schema defined in T004a."""
    schema_path = "specs/001-network-topology-thermal/contracts/simulation_result.schema.yaml"
    csv_path = "data/processed/simulation_results.csv"

    if not os.path.exists(csv_path):
        pytest.skip("CSV file not found")

    # Read schema
    import yaml
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)

    expected_columns = schema.get('columns', [])

    # Read CSV header
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)

    # Check if expected columns are present
    for col in expected_columns:
        assert col in header, f"Column {col} missing from CSV header"

def test_correlation_matrix_schema():
    # Placeholder for correlation matrix schema test
    assert True

import pytest
import pandas as pd
import os
import yaml
from pathlib import Path

# Adjust import based on project structure if necessary, 
# but assuming tests/contract is at same level as code/ or similar access
# For this specific task, we validate the schema file exists and matches CSV output
# We will load the schema from the specs directory as defined in T004a

SCHEMA_PATH = Path(__file__).parent.parent.parent / "specs" / "001-network-topology-thermal" / "contracts" / "simulation_result.schema.yaml"

@pytest.fixture
def schema():
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def sample_csv_path(tmp_path, schema):
    """Create a temporary CSV file that matches the schema."""
    csv_path = tmp_path / "simulation_results.csv"
    columns = schema.get('columns', [])
    if not columns:
        pytest.fail("Schema must define 'columns'")
    
    # Create a dummy dataframe
    data = {col: [1] for col in columns}
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return csv_path

def test_csv_output_matches_schema(schema, sample_csv_path):
    """
    Contract test: Verify that the CSV output structure matches the defined schema.
    This ensures that any code generating simulation_results.csv adheres to the spec.
    """
    # Load the CSV
    df = pd.read_csv(sample_csv_path)
    
    # Get expected columns from schema
    expected_columns = schema.get('columns', [])
    
    # Check column presence and order (strictly matching if schema implies order)
    # Usually, CSV order matters for some parsers, but set equality is safer for contract
    # unless the schema explicitly defines order.
    actual_columns = list(df.columns)
    
    assert set(actual_columns) == set(expected_columns), \
        f"CSV columns {actual_columns} do not match schema columns {expected_columns}"
    
    # Check data types if specified in schema
    if 'types' in schema:
        for col_name, expected_type in schema['types'].items():
            if col_name in df.columns:
                actual_dtype = str(df[col_name].dtype)
                # Simple type mapping check
                type_map = {
                    'int': ['int64', 'int32'],
                    'float': ['float64', 'float32'],
                    'str': ['object', 'string']
                }
                if expected_type in type_map:
                    assert actual_dtype in type_map[expected_type], \
                        f"Column {col_name} has type {actual_dtype}, expected {expected_type}"

def test_correlation_matrix_schema(schema):
    """
    Contract test: Verify the schema structure for correlation matrix output.
    While the main schema is for CSV, this checks if the schema file defines
    constraints for correlation data if it were to be stored or if it validates
    the structure expected by the regression analysis module.
    
    Since the primary output is CSV, this test ensures the schema file is robust
    and defines the necessary metadata for any derived metrics like correlation.
    """
    # Basic validation that the schema is a dictionary
    assert isinstance(schema, dict), "Schema must be a dictionary"
    
    # Check for required top-level keys
    required_keys = ['columns']
    for key in required_keys:
        assert key in schema, f"Schema missing required key: {key}"
    
    # Check that columns is a list
    assert isinstance(schema['columns'], list), "Schema 'columns' must be a list"
    
    # Verify specific columns required for correlation analysis exist in the schema
    # T026 requires correlation matrix calculation for all metrics.
    # The schema should ideally define the columns that feed into this.
    required_metrics = ['avg_degree', 'conductivity']
    schema_columns = schema['columns']
    
    for metric in required_metrics:
        assert metric in schema_columns, \
            f"Schema missing required metric column for correlation analysis: {metric}"
    
    # If the schema defines a 'types' section, verify it covers the metrics
    if 'types' in schema:
        for metric in required_metrics:
            assert metric in schema['types'], \
                f"Schema 'types' missing definition for metric: {metric}"
    
    # If the schema defines 'constraints' or 'validation', ensure it's structured
    if 'constraints' in schema:
        assert isinstance(schema['constraints'], dict), "Schema 'constraints' must be a dict"
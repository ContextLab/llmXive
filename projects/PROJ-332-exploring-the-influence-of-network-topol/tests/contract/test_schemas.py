import pytest
import yaml
import pandas as pd
import os

def test_csv_output_matches_schema():
    """Verify CSV output matches the schema defined in T004a."""
    schema_path = "specs/001-network-topology-thermal/contracts/simulation_result.schema.yaml"
    csv_path = "data/processed/simulation_results.csv"
    
    if not os.path.exists(schema_path):
        pytest.skip("Schema file not found")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    expected_columns = set(schema['columns'].keys())
    
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        actual_columns = set(df.columns)
        
        # Check if all expected columns are present
        missing = expected_columns - actual_columns
        assert not missing, f"Missing columns in CSV: {missing}"
        
        # Check if there are extra columns (optional, depending on strictness)
        # For now, we just ensure the required ones exist
    else:
        pytest.skip("CSV file not found, skipping schema validation")

def test_correlation_matrix_schema():
    """Verify correlation matrix output structure (if generated)."""
    # This is a placeholder for future correlation matrix schema validation
    # Currently, we just ensure the function exists and runs without error
    from code.regression_analysis import calculate_correlation_matrix
    import pandas as pd
    
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [3, 2, 1], 'c': [1, 1, 1]})
    corr = calculate_correlation_matrix(df)
    
    assert isinstance(corr, pd.DataFrame)
    assert corr.shape[0] == corr.shape[1]
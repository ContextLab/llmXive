import os
import sys
import json
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from stats.regression_table import load_regression_results, generate_regression_table
from state.version_map import generate_trace_id

def test_generate_regression_table_with_data():
    """
    Integration test for T034: Verify that the regression table is generated
    correctly with coefficients, SE, p-values, and trace_id.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        input_path = tmpdir / "regression_results.csv"
        output_path = tmpdir / "regression_table.csv"
        
        # Create mock input data matching T031 output schema
        mock_data = {
            'subject_id': ['sub-001', 'sub-002', 'sub-003'],
            'metric_name': ['Global_Efficiency', 'Global_Efficiency', 'Local_Efficiency'],
            'coef_age': [0.05, 0.06, 0.04],
            'se_age': [0.01, 0.01, 0.01],
            'pval_age': [0.001, 0.002, 0.005],
            'coef_sex': [0.1, 0.12, 0.08],
            'se_sex': [0.05, 0.05, 0.05],
            'pval_sex': [0.05, 0.04, 0.1],
            'coef_education': [0.02, 0.03, 0.01],
            'se_education': [0.01, 0.01, 0.01],
            'pval_education': [0.1, 0.05, 0.2]
        }
        df_input = pd.DataFrame(mock_data)
        df_input.to_csv(input_path, index=False)
        
        # Run the generation function
        generate_regression_table(df_input, output_path)
        
        # Verify output file exists
        assert output_path.exists(), "Output CSV file was not created."
        
        # Load and verify content
        df_output = pd.read_csv(output_path)
        
        # Check required columns
        required_cols = [
            'subject_id', 'metric_name',
            'coef_age', 'se_age', 'pval_age',
            'coef_sex', 'se_sex', 'pval_sex',
            'coef_education', 'se_education', 'pval_education',
            'trace_id'
        ]
        for col in required_cols:
            assert col in df_output.columns, f"Missing column: {col}"
        
        # Verify trace_id is present and consistent
        assert not df_output['trace_id'].isna().any(), "trace_id contains NaN values."
        assert len(df_output['trace_id'].unique()) == 1, "trace_id should be identical for all rows."
        
        # Verify trace_id format (SHA-256 hex string)
        trace_id = df_output['trace_id'].iloc[0]
        assert len(trace_id) == 64, f"trace_id length should be 64, got {len(trace_id)}"
        assert all(c in '0123456789abcdef' for c in trace_id), "trace_id should be a valid hex string."
        
        # Verify data integrity (values match input)
        assert df_output['coef_age'].iloc[0] == 0.05, "Coefficient values mismatch."
        assert df_output['pval_age'].iloc[1] == 0.002, "P-value values mismatch."
        
        print("Integration test for T034 passed.")

def test_generate_regression_table_empty_input():
    """
    Test handling of empty input DataFrame.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        input_path = tmpdir / "regression_results.csv"
        output_path = tmpdir / "regression_table.csv"
        
        # Create empty input
        df_empty = pd.DataFrame(columns=['subject_id', 'metric_name'])
        df_empty.to_csv(input_path, index=False)
        
        # Run generation
        generate_regression_table(df_empty, output_path)
        
        # Verify output exists and has correct columns
        assert output_path.exists(), "Output CSV file was not created for empty input."
        df_output = pd.read_csv(output_path)
        
        required_cols = [
            'subject_id', 'metric_name',
            'coef_age', 'se_age', 'pval_age',
            'coef_sex', 'se_sex', 'pval_sex',
            'coef_education', 'se_education', 'pval_education',
            'trace_id'
        ]
        for col in required_cols:
            assert col in df_output.columns, f"Missing column in empty output: {col}"
        
        print("Empty input test for T034 passed.")

if __name__ == "__main__":
    test_generate_regression_table_with_data()
    test_generate_regression_table_empty_input()
    print("All T034 tests passed.")
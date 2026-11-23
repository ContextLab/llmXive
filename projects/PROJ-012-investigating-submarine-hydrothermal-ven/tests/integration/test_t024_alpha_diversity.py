import pytest
import pandas as pd
import os
from pathlib import Path
import tempfile
import json

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))
from analysis import run_analysis_pipeline, load_transformed_diversity_data, run_lme_model

def test_t024_alpha_diversity_generation():
    """
    Test that T024 generates the expected output file with correct columns.
    """
    # Create a temporary directory for test data
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create mock input data (simulating T021 output)
        input_file = tmpdir / "diversity_transformed.csv"
        mock_data = {
            'sample_id': ['S001', 'S002', 'S003', 'S004', 'S005', 'S006', 'S007', 'S008', 'S009', 'S010'],
            'pH': [5.5, 6.2, 4.8, 7.0, 5.0, 6.5, 4.5, 7.5, 5.8, 6.8],
            'shannon': [3.2, 3.5, 2.9, 3.8, 3.0, 3.6, 2.7, 4.0, 3.4, 3.7],
            'simpson': [0.85, 0.90, 0.78, 0.92, 0.80, 0.91, 0.75, 0.94, 0.88, 0.93],
            'site': ['SiteA', 'SiteA', 'SiteB', 'SiteB', 'SiteA', 'SiteB', 'SiteA', 'SiteB', 'SiteA', 'SiteB'],
            'transformed_shannon': [3.1, 3.4, 2.8, 3.7, 2.9, 3.5, 2.6, 3.9, 3.3, 3.6]
        }
        df_input = pd.DataFrame(mock_data)
        df_input.to_csv(input_file, index=False)
        
        output_file = tmpdir / "alpha_diversity_results.csv"
        
        # Run the pipeline
        run_analysis_pipeline(str(input_file), str(output_file))
        
        # Verify output exists
        assert output_file.exists(), "Output file was not created."
        
        # Verify content
        df_output = pd.read_csv(output_file)
        
        # Check required columns
        required_cols = ['sample_id', 'pH', 'shannon', 'simpson', 'transformed_shannon', 
                         'estimate', 'se', 'p_value', 'model_type', 'nonlinearity_suggestion']
        for col in required_cols:
            assert col in df_output.columns, f"Missing column: {col}"
        
        # Check row count matches input
        assert len(df_output) == len(df_input), "Row count mismatch."
        
        # Check that LME stats are consistent across rows (global model)
        assert df_output['estimate'].nunique() == 1, "LME estimate should be constant across rows."
        assert df_output['model_type'].nunique() == 1, "Model type should be constant across rows."
        
        # Check that p_value is a number
        assert pd.to_numeric(df_output['p_value'], errors='coerce').notna().all(), "p-values must be numeric."

def test_t024_small_sample_fallback():
    """
    Test that T024 falls back to Spearman correlation when N < 10.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        input_file = tmpdir / "diversity_transformed.csv"
        # Only 5 samples
        mock_data = {
            'sample_id': ['S001', 'S002', 'S003', 'S004', 'S005'],
            'pH': [5.5, 6.2, 4.8, 7.0, 5.0],
            'shannon': [3.2, 3.5, 2.9, 3.8, 3.0],
            'simpson': [0.85, 0.90, 0.78, 0.92, 0.80],
            'site': ['SiteA', 'SiteA', 'SiteB', 'SiteB', 'SiteA'],
            'transformed_shannon': [3.1, 3.4, 2.8, 3.7, 2.9]
        }
        df_input = pd.DataFrame(mock_data)
        df_input.to_csv(input_file, index=False)
        
        output_file = tmpdir / "alpha_diversity_results.csv"
        
        run_analysis_pipeline(str(input_file), str(output_file))
        
        df_output = pd.read_csv(output_file)
        
        # Check model type is Spearman
        assert df_output['model_type'].iloc[0] == 'Spearman', "Should fallback to Spearman for N < 10."

def test_t024_single_site_fallback():
    """
    Test that T024 falls back to Fixed Effects when < 2 sites.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        input_file = tmpdir / "diversity_transformed.csv"
        # Only 1 site
        mock_data = {
            'sample_id': ['S001', 'S002', 'S003', 'S004', 'S005', 'S006', 'S007', 'S008', 'S009', 'S010'],
            'pH': [5.5, 6.2, 4.8, 7.0, 5.0, 6.5, 4.5, 7.5, 5.8, 6.8],
            'shannon': [3.2, 3.5, 2.9, 3.8, 3.0, 3.6, 2.7, 4.0, 3.4, 3.7],
            'simpson': [0.85, 0.90, 0.78, 0.92, 0.80, 0.91, 0.75, 0.94, 0.88, 0.93],
            'site': ['SiteA', 'SiteA', 'SiteA', 'SiteA', 'SiteA', 'SiteA', 'SiteA', 'SiteA', 'SiteA', 'SiteA'],
            'transformed_shannon': [3.1, 3.4, 2.8, 3.7, 2.9, 3.5, 2.6, 3.9, 3.3, 3.6]
        }
        df_input = pd.DataFrame(mock_data)
        df_input.to_csv(input_file, index=False)
        
        output_file = tmpdir / "alpha_diversity_results.csv"
        
        run_analysis_pipeline(str(input_file), str(output_file))
        
        df_output = pd.read_csv(output_file)
        
        # Check model type is FixedEffects
        assert df_output['model_type'].iloc[0] == 'FixedEffects', "Should fallback to FixedEffects for 1 site."

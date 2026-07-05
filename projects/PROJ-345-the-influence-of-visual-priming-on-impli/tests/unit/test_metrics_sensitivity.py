import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

from models.metrics import (
    calculate_sensitivity_analysis, 
    run_sensitivity_analysis,
    benjamini_hochberg
)

class TestSensitivityAnalysis:
    
    def test_calculate_sensitivity_analysis_basic(self):
        """Test basic functionality with known p-values."""
        # Create a dataframe with specific p-values
        # 5 tests: 0.001, 0.02, 0.04, 0.06, 0.20
        data = {
            'term': ['A', 'B', 'C', 'D', 'E'],
            'p_value': [0.001, 0.02, 0.04, 0.06, 0.20]
        }
        df = pd.DataFrame(data)
        
        alphas = [0.05, 0.10]
        result = calculate_sensitivity_analysis(df, p_column='p_value', alphas=alphas)
        
        assert 'alpha' in result.columns
        assert 'significance_rate' in result.columns
        
        # At alpha=0.05: 3 significant (0.001, 0.02, 0.04) -> rate = 3/5 = 0.6
        row_05 = result[result['alpha'] == 0.05]
        assert len(row_05) == 1
        assert row_05['significance_rate'].values[0] == 0.6
        
        # At alpha=0.10: 4 significant (0.001, 0.02, 0.04, 0.06) -> rate = 4/5 = 0.8
        row_010 = result[result['alpha'] == 0.10]
        assert len(row_010) == 1
        assert row_010['significance_rate'].values[0] == 0.8

    def test_calculate_sensitivity_analysis_no_significant(self):
        """Test when no p-values are significant at given alpha."""
        data = {'p_value': [0.5, 0.6, 0.7]}
        df = pd.DataFrame(data)
        
        result = calculate_sensitivity_analysis(df, alphas=[0.05])
        
        assert result['significance_rate'].values[0] == 0.0

    def test_calculate_sensitivity_analysis_all_significant(self):
        """Test when all p-values are significant."""
        data = {'p_value': [0.001, 0.002, 0.003]}
        df = pd.DataFrame(data)
        
        result = calculate_sensitivity_analysis(df, alphas=[0.05])
        
        assert result['significance_rate'].values[0] == 1.0

    def test_run_sensitivity_analysis_io(self):
        """Test that run_sensitivity_analysis writes file correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"
            
            # Create fake input
            data = {'p_value': [0.01, 0.04, 0.09, 0.15]}
            pd.DataFrame(data).to_csv(input_path, index=False)
            
            # Run
            run_sensitivity_analysis(input_path, output_path, alphas=[0.05, 0.10])
            
            # Verify output exists
            assert output_path.exists()
            
            # Verify content
            out_df = pd.read_csv(output_path)
            assert 'alpha' in out_df.columns
            assert 'significance_rate' in out_df.columns
            
            # Check specific values
            # 0.05: 2 sig (0.01, 0.04) -> 0.5
            # 0.10: 3 sig (0.01, 0.04, 0.09) -> 0.75
            row_05 = out_df[out_df['alpha'] == 0.05]
            assert abs(row_05['significance_rate'].values[0] - 0.5) < 1e-6
            
            row_010 = out_df[out_df['alpha'] == 0.10]
            assert abs(row_010['significance_rate'].values[0] - 0.75) < 1e-6

    def test_run_sensitivity_analysis_missing_input(self):
        """Test that missing input file raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "nonexistent.csv"
            output_path = Path(tmpdir) / "output.csv"
            
            with pytest.raises(FileNotFoundError):
                run_sensitivity_analysis(input_path, output_path)

    def test_default_alphas(self):
        """Test that default alphas are used if not provided."""
        data = {'p_value': [0.001, 0.01, 0.05, 0.10, 0.20]}
        df = pd.DataFrame(data)
        
        result = calculate_sensitivity_analysis(df)
        
        # Default alphas: [0.001, 0.01, 0.05, 0.10]
        expected_alphas = [0.001, 0.01, 0.05, 0.10]
        assert list(result['alpha']) == expected_alphas

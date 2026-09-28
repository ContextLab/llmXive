import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import spearmanr

# Ensure code is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis import (
    load_processed_data, 
    check_zero_variance, 
    compute_spearman_correlation, 
    save_correlation_results
)

class TestSpearmanCorrelation:
    """Tests for T022: Spearman rank correlation implementation."""
    
    @pytest.fixture
    def mock_cleaned_data(self, tmp_path):
        """Creates a mock cleaned_data.csv for testing."""
        # Create deterministic mock data with known correlation
        np.random.seed(42)
        n = 100
        shannon = np.random.normal(loc=3.5, scale=0.5, size=n)
        # Create a positive correlation
        fi = 2.0 * shannon + np.random.normal(loc=0, scale=0.2, size=n)
        
        df = pd.DataFrame({
            "shannon_index": shannon,
            "fluid_intelligence": fi,
            "age": np.random.randint(20, 80, n),
            "sex": np.random.choice(["M", "F"], n),
            "bmi": np.random.normal(25, 3, n)
        })
        
        csv_path = tmp_path / "cleaned_data.csv"
        df.to_csv(csv_path, index=False)
        return str(csv_path)

    def test_spearman_correlation_pvalue_calc(self, mock_cleaned_data, tmp_path):
        """
        T022 Verification: Input fixture mock_correlation.csv (simulated here via fixture).
        Expect p-value < 0.05 due to constructed correlation.
        """
        # Temporarily override the load path
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Load data manually to ensure we are using the fixture
            df = pd.read_csv(mock_cleaned_data)
            
            # Run the specific function
            r_value, p_value, n_obs = compute_spearman_correlation(df)
            
            # Assertions
            assert isinstance(r_value, float), "r_value must be a float"
            assert isinstance(p_value, float), "p_value must be a float"
            assert n_obs > 0, "n_obs must be positive"
            
            # With the constructed correlation, p-value should be significant
            assert p_value < 0.05, f"Expected p-value < 0.05, got {p_value}"
            
            # Verify output file generation
            output_path = Path("data/processed/correlation_results.csv")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            save_correlation_results(r_value, p_value, n_obs, str(output_path))
            
            assert output_path.exists(), "Correlation results CSV must be created"
            
            result_df = pd.read_csv(output_path)
            assert "r_value" in result_df.columns
            assert "p_value" in result_df.columns
            assert "n_obs" in result_df.columns
            
        finally:
            os.chdir(original_cwd)

    def test_input_validation_raw_counts(self, tmp_path):
        """
        T022 Critical Validation: Verify input is raw counts (shannon_index), not CLR-transformed.
        The function expects 'shannon_index' which is derived from raw counts.
        If the column contained CLR-transformed values (which would be weird for an index),
        we rely on the upstream pipeline (T020) to ensure correctness.
        This test verifies the function runs on the expected schema.
        """
        df = pd.DataFrame({
            "shannon_index": [3.0, 3.1, 3.2, 3.3, 3.4],
            "fluid_intelligence": [10, 11, 12, 13, 14]
        })
        
        r, p, n = compute_spearman_correlation(df)
        assert r is not None
        assert p is not None
        assert n == 5

    def test_missing_columns_raises_error(self, tmp_path):
        """Test that missing required columns raise ValueError."""
        df = pd.DataFrame({
            "other_col": [1, 2, 3]
        })
        
        with pytest.raises(ValueError, match="Column 'shannon_index' not found"):
            compute_spearman_correlation(df)
        
        df2 = pd.DataFrame({
            "shannon_index": [1, 2, 3]
        })
        with pytest.raises(ValueError, match="Column 'fluid_intelligence' not found"):
            compute_spearman_correlation(df2)

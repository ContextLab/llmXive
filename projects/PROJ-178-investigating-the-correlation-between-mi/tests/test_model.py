import os
import sys
import pytest
import pandas as pd
from pathlib import Path
import yaml
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from analysis.model import calculate_rank_ols, calculate_unadjusted_spearman, apply_benjamini_hochberg

def load_schema():
    """Load the output schema for validation."""
    schema_path = project_root / "code" / "contracts" / "output.schema.yaml"
    if not schema_path.exists():
        # Fallback if schema not created yet, but task T006B should have created it
        return {
            "type": "object",
            "properties": {
                "method": {"type": "string"},
                "coefficient": {"type": "number"},
                "p_value": {"type": "number"}
            }
        }
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def load_dataset():
    """
    Load the processed dataset. If not present, create a minimal synthetic one
    strictly for testing the logic of the function (not for final results).
    This is allowed here because we are unit testing the function logic,
    not running the full pipeline on real data.
    """
    data_path = project_root / "code" / "data" / "processed" / "mito_aging_dataset.csv"
    if data_path.exists():
        return pd.read_csv(data_path)
    
    # Create synthetic test data for unit tests
    # This mimics the expected columns
    data = {
        'heteroplasmy_burden': [0.01, 0.02, 0.03, 0.04, 0.05],
        'age': [20, 30, 40, 50, 60],
        'sequencing_depth': [100, 120, 110, 130, 140],
        'PC1': [0.1, 0.2, 0.3, 0.4, 0.5],
        'PC2': [0.2, 0.3, 0.4, 0.5, 0.6],
        'sex': ['M', 'F', 'M', 'F', 'M']
    }
    return pd.DataFrame(data)

class TestStatisticalOutputSchema:
    """Contract test for statistical output schema."""
    
    def test_spearman_output_structure(self):
        df = load_dataset()
        result = calculate_unadjusted_spearman(df)
        
        assert 'method' in result
        assert result['method'] == 'unadjusted_spearman'
        assert 'coefficient' in result
        assert 'p_value' in result
        assert isinstance(result['coefficient'], float)
        assert isinstance(result['p_value'], float)
    
    def test_rank_ols_output_structure(self):
        df = load_dataset()
        result, _ = calculate_rank_ols(df)
        
        assert 'method' in result
        assert result['method'] == 'rank_ols'
        assert 'coefficient' in result
        assert 'p_value' in result
        assert 'formula' in result
        assert isinstance(result['coefficient'], float)
        assert isinstance(result['p_value'], float)

class TestRankOLSImplementation:
    """Integration test for Rank-OLS implementation."""
    
    def test_rank_ols_recovers_positive_correlation(self):
        """
        Test that Rank-OLS recovers a positive coefficient when data is positively correlated.
        We create a synthetic dataset where age and burden are perfectly correlated.
        """
        data = {
            'heteroplasmy_burden': [1, 2, 3, 4, 5],
            'age': [10, 20, 30, 40, 50],
            'sequencing_depth': [100, 100, 100, 100, 100],
            'PC1': [0, 0, 0, 0, 0],
            'PC2': [0, 0, 0, 0, 0],
            'sex': ['M', 'M', 'M', 'M', 'M']
        }
        df = pd.DataFrame(data)
        
        result, model = calculate_rank_ols(df)
        
        # Coefficient should be positive
        assert result['coefficient'] > 0
        # P-value should be very small (highly significant)
        assert result['p_value'] < 0.05
        
    def test_rank_ols_handles_categorical_sex(self):
        """Test that the model correctly handles the 'sex' categorical variable."""
        data = {
            'heteroplasmy_burden': [1, 2, 3, 4, 5, 6],
            'age': [10, 20, 30, 40, 50, 60],
            'sequencing_depth': [100, 100, 100, 100, 100, 100],
            'PC1': [0, 0, 0, 0, 0, 0],
            'PC2': [0, 0, 0, 0, 0, 0],
            'sex': ['M', 'F', 'M', 'F', 'M', 'F']
        }
        df = pd.DataFrame(data)
        
        # Should not raise an error
        result, model = calculate_rank_ols(df)
        assert result['coefficient'] is not None
        
    def test_benjamini_hochberg_adjustment(self):
        """Test BH correction logic."""
        pvals = [0.01, 0.04, 0.03, 0.20, 0.005]
        adjusted = apply_benjamini_hochberg(pvals)
        
        # Adjusted p-values should be >= original p-values
        for orig, adj in zip(pvals, adjusted):
            assert adj >= orig
        
        # Last adjusted p-value should be 1.0 or close to it if it was large
        # (Monotonicity check)
        for i in range(len(adjusted) - 1):
            assert adjusted[i] <= adjusted[i+1] or abs(adjusted[i] - adjusted[i+1]) < 1e-10
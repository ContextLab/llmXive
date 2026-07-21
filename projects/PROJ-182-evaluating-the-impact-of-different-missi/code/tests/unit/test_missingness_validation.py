import pytest
import pandas as pd
import numpy as np
from scipy import stats
from src.generators.missingness import (
    apply_mcar_mask, 
    apply_mar_mask, 
    apply_mnar_mask, 
    validate_missingness_pattern
)

@pytest.fixture
def sample_data():
    """Create a sample dataframe for testing."""
    np.random.seed(42)
    n = 1000
    df = pd.DataFrame({
        'X': np.random.uniform(-1, 1, n),
        'Z': np.random.normal(0, 1, n),
        'D': (np.random.uniform(-1, 1, n) > 0).astype(int),
        'Y': np.random.normal(0, 1, n)
    })
    return df

class TestMCARValidation:
    def test_mcar_independence(self, sample_data):
        """Test that MCAR mask is independent of all variables."""
        df = sample_data.copy()
        df = apply_mcar_mask(df, rate=0.2, seed=123)
        
        is_valid, p_val, message = validate_missingness_pattern(df, 'MCAR')
        
        assert is_valid, f"MCAR validation failed: {message}"
        assert p_val >= 0.05, f"MCAR p-value should be >= 0.05, got {p_val}"

class TestMARValidation:
    def test_mar_dependency_on_z(self, sample_data):
        """Test that MAR mask depends on Z."""
        df = sample_data.copy()
        df = apply_mar_mask(df, rate=0.2, seed=123)
        
        is_valid, p_val, message = validate_missingness_pattern(df, 'MAR')
        
        assert is_valid, f"MAR validation failed: {message}"
        assert p_val < 0.05, f"MAR p-value should be < 0.05, got {p_val}"

class TestMNARValidation:
    def test_mnar_dependency_on_y(self, sample_data):
        """Test that MNAR mask depends on Y."""
        df = sample_data.copy()
        df = apply_mnar_mask(df, rate=0.2, seed=123)
        
        is_valid, p_val, message = validate_missingness_pattern(df, 'MNAR')
        
        assert is_valid, f"MNAR validation failed: {message}"
        assert p_val < 0.05, f"MNAR p-value should be < 0.05, got {p_val}"

class TestValidationEdgeCases:
    def test_missing_mask_column(self, sample_data):
        """Test validation fails when mask column is missing."""
        df = sample_data.copy()
        
        is_valid, p_val, message = validate_missingness_pattern(df, 'MCAR')
        
        assert not is_valid
        assert "No missingness mask found" in message

    def test_invalid_mechanism(self, sample_data):
        """Test validation fails for unknown mechanism."""
        df = sample_data.copy()
        df = apply_mcar_mask(df, rate=0.2, seed=123)
        
        is_valid, p_val, message = validate_missingness_pattern(df, 'UNKNOWN')
        
        assert not is_valid
        assert "Unknown mechanism" in message
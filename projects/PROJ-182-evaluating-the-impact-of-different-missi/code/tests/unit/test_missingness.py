import pytest
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
import sys

# Add project root to path for imports if running standalone
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.generators.missingness import apply_mar_mask, apply_mcar_mask, apply_mnar_mask
from src.generators.rd_data import generate_rd_data
from src.config_loader import load_missingness_config

@pytest.fixture
def synthetic_data():
    """Generate a deterministic synthetic dataset for testing missingness mechanisms."""
    # Use a fixed seed for reproducibility
    np.random.seed(42)
    config_dict = {
        "sample_size": 1000,
        "true_effect": 2.0,
        "seed": 42,
        "beta0": 0.0,
        "beta1": 1.0,
        "beta2": 0.5,
        "sigma": 0.5
    }
    data = generate_rd_data(config_dict)
    return data

class TestMCARValidation:
    """Tests for MCAR mechanism (Task T010) - verifying independence."""

    def test_mcar_independence_chi_square(self, synthetic_data):
        """
        Verify that MCAR mask is independent of the running variable X.
        For MCAR, the probability of missingness should be the same regardless of X.
        We use a Chi-square test of independence between X (binned) and Missingness.
        """
        rate = 0.3
        mask = apply_mcar_mask(synthetic_data.copy(), rate, seed=123)
        
        # Bin X into quartiles to create categorical variable for Chi-square
        synthetic_data['X_bin'] = pd.qcut(synthetic_data['X'], q=4, labels=False)
        mask['X_bin'] = synthetic_data['X_bin']
        
        # Create contingency table: Observed vs Missing by X_bin
        # 0 = Observed, 1 = Missing
        contingency = pd.crosstab(mask['X_bin'], mask['Y_missing'])
        
        # Perform Chi-square test
        chi2, p_value, dof, expected = stats.chi2_contingency(contingency)
        
        # For MCAR, we expect independence -> high p-value (fail to reject null)
        # Acceptance criterion: p > 0.05
        assert p_value > 0.05, f"MCAR failed independence test: p_value={p_value:.4f} <= 0.05"

class TestMARValidation:
    """Tests for MAR mechanism (Task T011) - verifying correlation with covariate Z."""

    def test_mar_correlation_with_covariate_z(self, synthetic_data):
        """
        Verify that MAR mask is correlated with the covariate Z.
        For MAR, missingness depends on Z. We test the correlation between Z and the missingness indicator.
        """
        rate = 0.3
        # Apply MAR mask: missingness depends on Z
        mask = apply_mar_mask(synthetic_data.copy(), rate, seed=456)
        
        # Calculate point-biserial correlation between Z (continuous) and Y_missing (binary)
        # This is equivalent to Pearson correlation for binary/continuous
        correlation, p_value = stats.pointbiserialr(
            mask['Y_missing'], 
            mask['Z']
        )
        
        # For MAR, we expect significant correlation -> low p-value (reject null)
        # Acceptance criterion: p < 0.05
        assert p_value < 0.05, f"MAR failed correlation test: p_value={p_value:.4f} >= 0.05"
        assert abs(correlation) > 0.0, f"MAR correlation should be non-zero, got {correlation}"

    def test_mar_target_rate_accuracy(self, synthetic_data):
        """Verify that MAR mechanism achieves the target missingness rate approximately."""
        target_rate = 0.4
        mask = apply_mar_mask(synthetic_data.copy(), target_rate, seed=789)
        
        actual_rate = mask['Y_missing'].mean()
        
        # Allow some tolerance due to stochastic nature and logistic mapping
        # The target is an asymptotic rate; with N=1000, we expect close match
        tolerance = 0.05
        assert abs(actual_rate - target_rate) < tolerance, \
            f"MAR rate mismatch: target={target_rate}, actual={actual_rate:.4f}, diff={abs(actual_rate - target_rate):.4f}"

class TestMNARValidation:
    """Tests for MNAR mechanism (Task T012) - verifying correlation with outcome Y."""

    def test_mnar_correlation_with_outcome_y(self, synthetic_data):
        """
        Verify that MNAR mask is correlated with the outcome Y.
        For MNAR, missingness depends on Y itself.
        """
        rate = 0.3
        # Apply MNAR mask: missingness depends on Y
        mask = apply_mnar_mask(synthetic_data.copy(), rate, seed=999)
        
        # Calculate point-biserial correlation between Y (continuous) and Y_missing (binary)
        correlation, p_value = stats.pointbiserialr(
            mask['Y_missing'], 
            mask['Y']
        )
        
        # For MNAR, we expect significant correlation -> low p-value
        # Acceptance criterion: p < 0.05
        assert p_value < 0.05, f"MNAR failed correlation test: p_value={p_value:.4f} >= 0.05"
        assert abs(correlation) > 0.0, f"MNAR correlation should be non-zero, got {correlation}"

    def test_mnar_target_rate_accuracy(self, synthetic_data):
        """Verify that MNAR mechanism achieves the target missingness rate approximately."""
        target_rate = 0.5
        mask = apply_mnar_mask(synthetic_data.copy(), target_rate, seed=111)
        
        actual_rate = mask['Y_missing'].mean()
        
        tolerance = 0.05
        assert abs(actual_rate - target_rate) < tolerance, \
            f"MNAR rate mismatch: target={target_rate}, actual={actual_rate:.4f}, diff={abs(actual_rate - target_rate):.4f}"

def test_generate_missingness_pattern_integration(synthetic_data):
    """
    Integration test for the main entry point of missingness generation.
    Ensures that the high-level function correctly dispatches to specific mechanisms.
    """
    from src.generators.missingness import generate_missingness_pattern
    
    # Test MCAR
    result_mcar = generate_missingness_pattern(synthetic_data.copy(), "MCAR", 0.3, seed=100)
    assert 'Y_missing' in result_mcar.columns
    assert result_mcar['Y_missing'].mean() > 0.0
    
    # Test MAR
    result_mar = generate_missingness_pattern(synthetic_data.copy(), "MAR", 0.3, seed=200)
    assert 'Y_missing' in result_mar.columns
    
    # Test MNAR
    result_mnar = generate_missingness_pattern(synthetic_data.copy(), "MNAR", 0.3, seed=300)
    assert 'Y_missing' in result_mnar.columns
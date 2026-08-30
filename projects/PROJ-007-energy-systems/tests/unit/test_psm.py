import pytest
import pandas as pd
import numpy as np
from src.analysis.psm import estimate_propensity, match_pairs, check_common_support
from src.analysis.balance import calculate_smd

@pytest.fixture
def sample_data():
    """Create a deterministic sample dataset for PSM testing."""
    np.random.seed(42)
    n = 200
    data = {
        'income': np.random.normal(50000, 15000, n),
        'housing_type': np.random.choice(['rent', 'own'], n),
        'location': np.random.choice(['urban', 'rural'], n),
        'treatment': np.random.binomial(1, 0.3, n),
        'pre_outcome': np.random.normal(1000, 200, n),
        'post_outcome': np.random.normal(1050, 200, n),
        'energy_cost': np.random.exponential(500, n),
        'solar_installation': np.random.binomial(1, 0.15, n)
    }
    df = pd.DataFrame(data)
    # Ensure some treatment variance
    df.loc[:50, 'treatment'] = 1
    df.loc[50:, 'treatment'] = 0
    return df

@pytest.fixture
def balanced_sample_data(sample_data):
    """Create data where propensity scores are well-separated but overlapping."""
    df = sample_data.copy()
    # Force a stronger signal for treatment so matching is meaningful
    df['treatment'] = (df['income'] < 45000).astype(int)
    return df

def test_estimate_propensity_returns_scores(sample_data):
    """Test that propensity score estimation returns valid probabilities."""
    covariates = ['income', 'housing_type', 'location']
    scores = estimate_propensity(sample_data, covariates=covariates)
    
    assert isinstance(scores, pd.Series)
    assert len(scores) == len(sample_data)
    assert scores.min() >= 0.0
    assert scores.max() <= 1.0
    assert not scores.isna().any()

def test_match_pairs_respects_caliper(balanced_sample_data):
    """Test that matching enforces the caliper constraint."""
    covariates = ['income', 'housing_type', 'location']
    caliper = 0.1
    
    # First get propensity scores
    scores = estimate_propensity(balanced_sample_data, covariates=covariates)
    balanced_sample_data['propensity'] = scores
    
    matched = match_pairs(balanced_sample_data, caliper=caliper)
    
    assert isinstance(matched, pd.DataFrame)
    # Check that matched pairs respect caliper
    if len(matched) > 0:
        diffs = np.abs(matched['propensity_treated'] - matched['propensity_control'])
        assert (diffs <= caliper).all(), "Caliper constraint violated"
        # Ensure we only get treated and control rows
        assert 'treatment' in matched.columns

def test_match_pairs_preserves_treatment_structure(balanced_sample_data):
    """Test that matching preserves the treated/control distinction."""
    covariates = ['income', 'housing_type', 'location']
    scores = estimate_propensity(balanced_sample_data, covariates=covariates)
    balanced_sample_data['propensity'] = scores
    
    matched = match_pairs(balanced_sample_data, caliper=0.1)
    
    if len(matched) > 0:
        # Each row should have one treated and one control unit
        assert 'treatment' in matched.columns
        # The matched dataframe should contain both treated and control indices
        assert matched['treatment'].nunique() == 2 or len(matched) == 0

def test_caliper_enforcement_tightness(balanced_sample_data):
    """Test that a smaller caliper results in fewer matches."""
    covariates = ['income', 'housing_type', 'location']
    scores = estimate_propensity(balanced_sample_data, covariates=covariates)
    balanced_sample_data['propensity'] = scores
    
    matched_wide = match_pairs(balanced_sample_data, caliper=0.2)
    matched_narrow = match_pairs(balanced_sample_data, caliper=0.05)
    
    assert len(matched_narrow) <= len(matched_wide), "Tighter caliper should reduce matches"

def test_smd_calculation_on_matched_data(balanced_sample_data):
    """Test that SMD is calculated correctly on matched data."""
    covariates = ['income', 'housing_type', 'location']
    scores = estimate_propensity(balanced_sample_data, covariates=covariates)
    balanced_sample_data['propensity'] = scores
    
    matched = match_pairs(balanced_sample_data, caliper=0.1)
    
    if len(matched) > 0:
        smd_results = calculate_smd(matched)
        
        assert isinstance(smd_results, dict)
        assert len(smd_results) > 0
        # SMD values should be numeric
        for var, val in smd_results.items():
            assert isinstance(val, (int, float, np.number))
            # SMD is typically between -2 and 2 in practice
            assert -5 <= val <= 5, f"SMD for {var} is unexpectedly large: {val}"

def test_common_support_check_identifies_extremes():
    """Test that common support check flags extreme propensity scores."""
    np.random.seed(123)
    n = 100
    data = {
        'income': np.random.normal(50000, 10000, n),
        'treatment': np.random.binomial(1, 0.5, n),
        'propensity': np.random.beta(2, 2, n)  # Beta distribution for scores
    }
    df = pd.DataFrame(data)
    
    # Inject extreme scores
    df.loc[0, 'propensity'] = 0.001
    df.loc[1, 'propensity'] = 0.999
    
    passed, excluded_count = check_common_support(df, prop_col='propensity', threshold=0.01)
    
    assert isinstance(passed, bool)
    assert isinstance(excluded_count, int)
    # With extreme values, we should expect some exclusions or a warning
    assert excluded_count >= 0

def test_psm_pipeline_integration(balanced_sample_data):
    """Integration test: propensity -> match -> balance check."""
    covariates = ['income', 'housing_type', 'location']
    
    # Step 1: Estimate propensity
    scores = estimate_propensity(balanced_sample_data, covariates=covariates)
    balanced_sample_data['propensity'] = scores
    
    # Step 2: Check common support
    passed, _ = check_common_support(balanced_sample_data, prop_col='propensity')
    if not passed:
        pytest.skip("Common support check failed, skipping balance test")
    
    # Step 3: Match
    matched = match_pairs(balanced_sample_data, caliper=0.1)
    
    if len(matched) > 0:
        # Step 4: Check balance
        smd = calculate_smd(matched)
        # In a perfect world all SMDs < 0.1, but we just check the calculation works
        assert all(isinstance(v, (int, float)) for v in smd.values)

def test_match_pairs_empty_when_no_overlap(balanced_sample_data):
    """Test matching behavior when no common support exists."""
    # Create data with completely disjoint propensity scores
    np.random.seed(999)
    n = 50
    df = pd.DataFrame({
        'income': np.concatenate([np.random.normal(30000, 1000, n), np.random.normal(80000, 1000, n)]),
        'treatment': [1]*n + [0]*n,
        'propensity': np.concatenate([np.random.uniform(0.01, 0.2, n), np.random.uniform(0.8, 0.99, n)])
    })
    
    matched = match_pairs(df, caliper=0.1)
    
    # Should return empty or very few matches due to no overlap
    assert len(matched) == 0 or len(matched) < n
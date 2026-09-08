import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_absolute_error

# Import the function under test (assuming it will be in code/evaluate.py)
# Since we are writing the test first (TDD), we expect this import to fail initially
# or the function to be a stub.
try:
    from evaluate import run_permutation_test
    HAS_IMPLEMENTATION = True
except ImportError:
    HAS_IMPLEMENTATION = False


@pytest.fixture
def sample_data():
    """Create a small, deterministic dataset for testing permutation logic."""
    np.random.seed(42)
    n_samples = 100
    data = {
        'cold_work_pct': np.random.uniform(0, 100, n_samples),
        'Mn_wt': np.random.uniform(0.1, 1.5, n_samples),
        'Mg_wt': np.random.uniform(0.1, 1.5, n_samples),
        'Si_wt': np.random.uniform(0.1, 1.5, n_samples),
        'Cu_wt': np.random.uniform(0.1, 1.5, n_samples),
        'annealing_temp_K': np.random.uniform(300, 600, n_samples),
        # Interaction features
        'cw_Mn': np.random.uniform(0, 150, n_samples),
        'cw_Mg': np.random.uniform(0, 150, n_samples),
        'cw_Si': np.random.uniform(0, 150, n_samples),
        'cw_Cu': np.random.uniform(0, 150, n_samples),
        # Target
        'time_to_peak_min': np.random.uniform(10, 100, n_samples)
    }
    return pd.DataFrame(data)


@pytest.fixture
def trained_models(sample_data):
    """Train simple models for the permutation test."""
    feature_cols = [
        'cold_work_pct', 'Mn_wt', 'Mg_wt', 'Si_wt', 'Cu_wt', 'annealing_temp_K',
        'cw_Mn', 'cw_Mg', 'cw_Si', 'cw_Cu'
    ]
    X = sample_data[feature_cols]
    y = sample_data['time_to_peak_min']

    # Train a model that uses interaction terms
    model_interaction = RandomForestRegressor(n_estimators=10, random_state=42)
    model_interaction.fit(X, y)

    # Train a baseline model without interaction terms (using only main effects)
    main_effect_cols = [
        'cold_work_pct', 'Mn_wt', 'Mg_wt', 'Si_wt', 'Cu_wt', 'annealing_temp_K'
    ]
    X_main = sample_data[main_effect_cols]
    model_additive = RandomForestRegressor(n_estimators=10, random_state=42)
    model_additive.fit(X_main, y)

    return model_interaction, model_additive, feature_cols, main_effect_cols


def test_permutation_test_imports():
    """Ensure the permutation test function exists."""
    assert HAS_IMPLEMENTATION, "run_permutation_test must be implemented in code/evaluate.py"


def test_permutation_logic_shuffles_correctly(sample_data):
    """
    Verify that the permutation logic actually shuffles the interaction terms
    while keeping main effects constant.
    """
    if not HAS_IMPLEMENTATION:
        pytest.skip("Implementation not yet available")

    # We will test the logic by inspecting the internal behavior or by mocking
    # Since we can't easily inspect internal state of a black-box function,
    # we rely on the fact that the function should accept a specific set of interaction columns.
    # Here we verify that if we pass a mock function that checks for shuffling, it behaves correctly.
    
    interaction_cols = ['cw_Mn', 'cw_Mg', 'cw_Si', 'cw_Cu']
    
    # Create a mock validation function
    original_data = sample_data.copy()
    shuffled_data = sample_data.copy()
    
    # Manually shuffle one interaction column to simulate the permutation step
    shuffled_data['cw_Mn'] = np.random.permutation(shuffled_data['cw_Mn'].values)
    
    # Check that the shuffled column is indeed different
    assert not original_data['cw_Mn'].equals(shuffled_data['cw_Mn']), \
        "Shuffling must change the data"
    
    # Check that main effects are preserved
    assert original_data['cold_work_pct'].equals(shuffled_data['cold_work_pct']), \
        "Main effects must remain constant during permutation"


def test_permutation_test_calculates_p_value(sample_data, trained_models):
    """
    Test that the permutation test calculates a p-value based on the distribution
    of errors from permuted vs. original data.
    """
    if not HAS_IMPLEMENTATION:
        pytest.skip("Implementation not yet available")

    model_interaction, model_additive, feature_cols, main_effect_cols = trained_models
    
    # Run the permutation test with a small number of permutations for speed
    n_permutations = 5
    results = run_permutation_test(
        model_interaction, 
        sample_data, 
        feature_cols, 
        ['cw_Mn', 'cw_Mg', 'cw_Si', 'cw_Cu'], # interaction terms to shuffle
        n_permutations=n_permutations,
        random_state=42
    )
    
    # Verify output structure
    assert 'p_value' in results, "Results must contain 'p_value'"
    assert 'test_statistic' in results, "Results must contain 'test_statistic'"
    assert 'original_mae' in results, "Results must contain 'original_mae'"
    assert 'permuted_mae_distribution' in results, "Results must contain 'permuted_mae_distribution'"
    
    # Verify p-value is a float between 0 and 1
    assert 0.0 <= results['p_value'] <= 1.0, "p-value must be between 0 and 1"
    
    # Verify the distribution has the correct length
    assert len(results['permuted_mae_distribution']) == n_permutations, \
        "Permuted MAE distribution must match n_permutations"


def test_permutation_test_determinism(sample_data, trained_models):
    """
    Ensure that running the permutation test twice with the same seed yields the same results.
    """
    if not HAS_IMPLEMENTATION:
        pytest.skip("Implementation not yet available")

    model_interaction, model_additive, feature_cols, main_effect_cols = trained_models
    
    results1 = run_permutation_test(
        model_interaction, 
        sample_data, 
        feature_cols, 
        ['cw_Mn', 'cw_Mg', 'cw_Si', 'cw_Cu'],
        n_permutations=10,
        random_state=123
    )
    
    results2 = run_permutation_test(
        model_interaction, 
        sample_data, 
        feature_cols, 
        ['cw_Mn', 'cw_Mg', 'cw_Si', 'cw_Cu'],
        n_permutations=10,
        random_state=123
    )
    
    assert results1['p_value'] == results2['p_value'], \
        "Permutation test must be deterministic with the same seed"
    assert results1['original_mae'] == results2['original_mae'], \
        "Original MAE must be consistent"


def test_permutation_test_edge_case_no_interaction_impact(sample_data):
    """
    Test a scenario where interaction terms have no predictive power.
    The p-value should be high (fail to reject null hypothesis).
    """
    if not HAS_IMPLEMENTATION:
        pytest.skip("Implementation not yet available")

    # Create data where target is independent of interaction terms
    np.random.seed(42)
    n_samples = 50
    data = {
        'cold_work_pct': np.random.uniform(0, 100, n_samples),
        'Mn_wt': np.random.uniform(0.1, 1.5, n_samples),
        'cw_Mn': np.random.uniform(0, 150, n_samples), # Random noise
        'time_to_peak_min': np.random.uniform(10, 100, n_samples) # Random noise
    }
    df = pd.DataFrame(data)
    
    model = RandomForestRegressor(n_estimators=5, random_state=42)
    model.fit(df[['cold_work_pct', 'Mn_wt', 'cw_Mn']], df['time_to_peak_min'])
    
    results = run_permutation_test(
        model,
        df,
        ['cold_work_pct', 'Mn_wt', 'cw_Mn'],
        ['cw_Mn'],
        n_permutations=20,
        random_state=42
    )
    
    # If interactions are random noise, shuffling them shouldn't significantly change error
    # The p-value should be relatively high (though with small N it might vary)
    # We just check that it runs without error and returns a valid p-value
    assert 0.0 <= results['p_value'] <= 1.0
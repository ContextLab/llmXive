"""
Integration tests for the simulation module focusing on baseline simulation loop
and p-value distribution generation for User Story 1.
"""

import os
import sys
import json
import tempfile
import numpy as np
import pandas as pd
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

import simulation
from simulation import (
    generate_type_i_condition,
    generate_type_ii_condition,
    run_hypothesis_test,
    run_simulation_iteration,
    run_full_simulation,
    save_results,
    validate_schema
)
from subsample import create_stratified_subsample, detect_target_column

# Constants for testing
TEST_ITERATIONS = 50  # Reduced for faster testing
TEST_SEED = 42
TEST_SAMPLE_SIZE = 25

def test_p_value_distribution_null_condition():
    """
    Integration test: Verify that running the simulation loop under the null condition
    generates a p-value distribution that is approximately uniform (or at least
    contains values across the range).
    """
    # Create a synthetic dataset with no true difference between classes
    # (This simulates the "Null" hypothesis scenario)
    np.random.seed(TEST_SEED)
    n_samples = 200
    n_features = 5
    
    X = np.random.randn(n_samples, n_features)
    y = np.random.randint(0, 2, n_samples)
    
    # Run the full simulation loop for null condition
    # Note: We use a small number of iterations for this test
    results = run_full_simulation(
        X=X,
        y=y,
        iterations=TEST_ITERATIONS,
        condition_type='null',
        seed=TEST_SEED,
        sample_size=TEST_SAMPLE_SIZE
    )
    
    # Verify output structure
    assert 'p_values' in results
    assert 'config' in results
    
    # Verify p-values are in valid range [0, 1]
    p_values = results['p_values']
    assert len(p_values) == TEST_ITERATIONS
    assert all(0.0 <= p <= 1.0 for p in p_values)
    
    # For a true null hypothesis, p-values should be roughly uniform.
    # We check that we don't have a degenerate distribution (e.g., all 1.0 or all 0.0)
    unique_vals = len(set(p_values))
    assert unique_vals > 1, "P-value distribution is degenerate (all same value)"
    
    # Check that we have some values < 0.05 (expected ~5% of the time)
    # With only 50 iterations, we might get 0 by chance, so we check for a reasonable range
    # rather than a strict statistical test for this unit test
    assert min(p_values) < 0.5, "P-values are suspiciously high for null condition"

def test_p_value_distribution_alt_condition():
    """
    Integration test: Verify that running the simulation loop under the alternative
    condition generates a p-value distribution skewed towards 0 (indicating power).
    """
    # Create a synthetic dataset with a clear difference between classes
    # (This simulates the "Alternative" hypothesis scenario)
    np.random.seed(TEST_SEED)
    n_samples = 200
    n_features = 5
    
    # Class 0 centered at 0, Class 1 centered at 2 (clear separation)
    X_class0 = np.random.randn(100, n_features)
    X_class1 = np.random.randn(100, n_features) + 2.0
    X = np.vstack([X_class0, X_class1])
    y = np.array([0] * 100 + [1] * 100)
    
    # Run the full simulation loop for alternative condition
    results = run_full_simulation(
        X=X,
        y=y,
        iterations=TEST_ITERATIONS,
        condition_type='alt',
        seed=TEST_SEED,
        sample_size=TEST_SAMPLE_SIZE
    )
    
    # Verify output structure
    assert 'p_values' in results
    assert 'config' in results
    
    # Verify p-values are in valid range
    p_values = results['p_values']
    assert len(p_values) == TEST_ITERATIONS
    assert all(0.0 <= p <= 1.0 for p in p_values)
    
    # For an alternative hypothesis, p-values should be skewed towards 0.
    # Check that the median is lower than for the null case
    median_p = np.median(p_values)
    assert median_p < 0.5, "P-value distribution for alt condition is not skewed towards 0"
    
    # Check that we have a significant portion of p-values < 0.05 (power)
    # With clear separation and 25 samples, we expect decent power
    low_p_count = sum(1 for p in p_values if p < 0.05)
    assert low_p_count > 0, "No significant results found for alternative condition (low power?)"

def test_simulation_save_and_load():
    """
    Integration test: Verify that simulation results can be saved to JSON and reloaded.
    """
    # Create simple data
    np.random.seed(TEST_SEED)
    X = np.random.randn(100, 3)
    y = np.random.randint(0, 2, 100)
    
    # Run simulation
    results = run_full_simulation(
        X=X,
        y=y,
        iterations=10,
        condition_type='null',
        seed=TEST_SEED,
        sample_size=20
    )
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        save_results(results, temp_path)
        
        # Verify file exists
        assert os.path.exists(temp_path), "Result file was not created"
        
        # Load and verify content
        with open(temp_path, 'r') as f:
            loaded_results = json.load(f)
        
        assert 'p_values' in loaded_results
        assert len(loaded_results['p_values']) == 10
        assert loaded_results['config']['iterations'] == 10
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_end_to_end_baseline_simulation():
    """
    End-to-end test: Simulate the baseline workflow (subsample -> simulate)
    to ensure the full loop works correctly for User Story 1.
    """
    # Create a dataset that mimics a real UCI dataset structure
    np.random.seed(TEST_SEED)
    n_samples = 150
    n_features = 4
    
    # Generate features with some correlation
    X = np.random.randn(n_samples, n_features)
    # Create a target column
    y = np.random.randint(0, 2, n_samples)
    
    # Combine into a DataFrame to mimic real data processing
    df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(n_features)])
    df['target'] = y
    
    # Detect target column (should find 'target')
    target_col = detect_target_column(df)
    assert target_col == 'target', f"Expected 'target', got {target_col}"
    
    # Create stratified subsample
    X_sub, y_sub = create_stratified_subsample(
        df=df,
        target_col='target',
        sample_size=20,
        seed=TEST_SEED
    )
    
    assert len(X_sub) == 20, f"Expected 20 samples, got {len(X_sub)}"
    assert len(y_sub) == 20, f"Expected 20 targets, got {len(y_sub)}"
    
    # Run baseline simulation (null condition)
    results = run_full_simulation(
        X=X_sub,
        y=y_sub,
        iterations=20,
        condition_type='null',
        seed=TEST_SEED,
        sample_size=20
    )
    
    # Verify results
    assert 'p_values' in results
    assert len(results['p_values']) == 20
    assert all(0.0 <= p <= 1.0 for p in results['p_values'])
    
    # Verify configuration metadata
    assert results['config']['condition_type'] == 'null'
    assert results['config']['sample_size'] == 20
    assert results['config']['iterations'] == 20

if __name__ == "__main__":
    # Run tests manually if executed as script
    test_p_value_distribution_null_condition()
    print("✓ test_p_value_distribution_null_condition passed")
    
    test_p_value_distribution_alt_condition()
    print("✓ test_p_value_distribution_alt_condition passed")
    
    test_simulation_save_and_load()
    print("✓ test_simulation_save_and_load passed")
    
    test_end_to_end_baseline_simulation()
    print("✓ test_end_to_end_baseline_simulation passed")
    
    print("\nAll integration tests passed!")
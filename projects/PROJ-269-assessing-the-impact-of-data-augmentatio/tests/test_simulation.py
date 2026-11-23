"""
Unit tests for the simulation module.
"""
import os
import sys
import json
import tempfile
import shutil
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent.parent))

from simulation import (
    run_full_simulation,
    validate_schema,
    load_dataset,
    generate_type_i_condition,
    generate_type_ii_condition,
    run_hypothesis_test,
    run_simulation_iteration,
    save_results,
    main
)
from subsample import create_stratified_subsample, detect_target_column
from download_data import compute_sha256

# Constants for testing
TEST_SEED = 42
TEST_ITERATIONS = 50  # Reduced for faster testing
TEST_SIZE = 15  # Small sample size for testing
TEST_DATA_DIR = Path("data/raw")
TEST_RESULTS_DIR = Path("results")
TEST_CONTRACTS_DIR = Path("contracts")

# Ensure directories exist for tests
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test directories."""
    os.makedirs(TEST_DATA_DIR, exist_ok=True)
    os.makedirs(TEST_RESULTS_DIR, exist_ok=True)
    os.makedirs(TEST_CONTRACTS_DIR, exist_ok=True)
    yield
    # Cleanup is optional in test environment to preserve state if needed

@pytest.fixture
def mock_dataset_path():
    """
    Create a minimal mock dataset for testing.
    In a real scenario, this would download actual UCI data.
    For T039, we need a deterministic dataset to verify reproducibility.
    """
    # Create a simple binary classification dataset
    np.random.seed(TEST_SEED)
    n_samples = 100
    n_features = 10
    
    # Generate features
    X = np.random.randn(n_samples, n_features)
    # Generate labels with some class imbalance
    y = np.random.binomial(1, 0.3, n_samples)
    
    # Create DataFrame
    df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(n_features)])
    df['target'] = y
    
    # Save to a temporary file
    temp_dir = tempfile.mkdtemp()
    dataset_path = Path(temp_dir) / 'test_dataset.csv'
    df.to_csv(dataset_path, index=False)
    
    yield dataset_path
    
    # Cleanup
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_schema_path():
    """Create a minimal simulation schema for testing."""
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "metadata": {
                "type": "object",
                "properties": {
                    "dataset": {"type": "string"},
                    "size": {"type": "integer"},
                    "seed": {"type": "integer"},
                    "condition": {"type": "string"}
                },
                "required": ["dataset", "size", "seed", "condition"]
            },
            "p_values": {
                "type": "array",
                "items": {"type": "number"}
            },
            "error_rates": {
                "type": "object",
                "properties": {
                    "type_i": {"type": "number"},
                    "type_ii": {"type": "number"}
                }
            }
        },
        "required": ["metadata", "p_values"]
    }
    
    temp_dir = tempfile.mkdtemp()
    schema_path = Path(temp_dir) / 'simulation_schema.json'
    with open(schema_path, 'w') as f:
        json.dump(schema, f)
    
    yield schema_path
    
    shutil.rmtree(temp_dir)

def test_deterministic_seed_reproducibility(mock_dataset_path, mock_schema_path):
    """
    T039: Test that running the baseline loop twice with the same seed
    produces bitwise identical p-value distributions.
    
    This ensures strict reproducibility as required by the task.
    """
    # Configuration for the test
    dataset_name = "test_reproducibility"
    size = TEST_SIZE
    seed = TEST_SEED
    iterations = TEST_ITERATIONS
    condition = "baseline"
    
    # Load the dataset
    df = load_dataset(str(mock_dataset_path))
    target_col = detect_target_column(df)
    
    # Create a subsample
    subsample_df = create_stratified_subsample(df, size, target_col)
    
    # Ensure we have enough samples for the test
    if len(subsample_df) < size:
        pytest.skip(f"Not enough samples for size {size}")
    
    # First run
    results_run1 = run_full_simulation(
        dataset=subsample_df,
        dataset_name=dataset_name,
        size=size,
        seed=seed,
        iterations=iterations,
        condition=condition,
        schema_path=mock_schema_path
    )
    
    # Second run with the exact same parameters
    results_run2 = run_full_simulation(
        dataset=subsample_df,
        dataset_name=dataset_name,
        size=size,
        seed=seed,
        iterations=iterations,
        condition=condition,
        schema_path=mock_schema_path
    )
    
    # Extract p-values from both runs
    p_values_run1 = results_run1['p_values']
    p_values_run2 = results_run2['p_values']
    
    # Verify that the p-value distributions are identical
    # Use np.allclose with very tight tolerance for bitwise comparison
    # Floating point operations should be deterministic with same seed
    assert len(p_values_run1) == len(p_values_run2), "P-value distributions have different lengths"
    
    # Check for exact bitwise equality (within floating point tolerance)
    # Using a very small tolerance to ensure reproducibility
    assert np.allclose(p_values_run1, p_values_run2, rtol=0, atol=0), \
        "P-value distributions are not bitwise identical with the same seed"
    
    # Also verify metadata is identical
    assert results_run1['metadata'] == results_run2['metadata'], \
        "Metadata differs between runs"
    
    # Verify error rates are identical
    assert results_run1['error_rates'] == results_run2['error_rates'], \
        "Error rates differ between runs"
    
    print(f"✓ Reproducibility test passed: {iterations} iterations with seed {seed} produced identical results")

def test_seed_affects_results(mock_dataset_path, mock_schema_path):
    """
    Verify that different seeds produce different results.
    This is a sanity check to ensure the seed parameter is actually used.
    """
    dataset_name = "test_seed_variation"
    size = TEST_SIZE
    iterations = TEST_ITERATIONS
    condition = "baseline"
    
    df = load_dataset(str(mock_dataset_path))
    target_col = detect_target_column(df)
    subsample_df = create_stratified_subsample(df, size, target_col)
    
    if len(subsample_df) < size:
        pytest.skip(f"Not enough samples for size {size}")
    
    # Run with seed 42
    results_seed_42 = run_full_simulation(
        dataset=subsample_df,
        dataset_name=dataset_name,
        size=size,
        seed=42,
        iterations=iterations,
        condition=condition,
        schema_path=mock_schema_path
    )
    
    # Run with seed 123
    results_seed_123 = run_full_simulation(
        dataset=subsample_df,
        dataset_name=dataset_name,
        size=size,
        seed=123,
        iterations=iterations,
        condition=condition,
        schema_path=mock_schema_path
    )
    
    # Verify that results are different (with high probability)
    p_values_42 = results_seed_42['p_values']
    p_values_123 = results_seed_123['p_values']
    
    # They should be different (unless by extremely rare chance)
    is_different = not np.allclose(p_values_42, p_values_123, rtol=0, atol=0)
    
    # We expect them to be different with very high probability
    # If they happen to be the same, it's a statistical fluke, so we'll be lenient
    # but log a warning
    if not is_different:
        print("⚠ Warning: Different seeds produced identical results (statistical fluke)")
    
    # For robustness, we'll check that at least some values differ
    # or that the distributions are statistically different
    assert is_different or np.mean(np.abs(np.array(p_values_42) - np.array(p_values_123))) > 1e-10, \
        "Different seeds should produce different results"

def test_schema_validation(mock_schema_path):
    """Test that the schema validation works correctly."""
    # Create a valid result
    valid_result = {
        "metadata": {
            "dataset": "test",
            "size": 15,
            "seed": 42,
            "condition": "baseline"
        },
        "p_values": [0.05, 0.1, 0.2],
        "error_rates": {"type_i": 0.1, "type_ii": 0.2}
    }
    
    # This should not raise an exception
    assert validate_schema(valid_result, mock_schema_path) is True

def test_schema_rejection(mock_schema_path):
    """Test that invalid results are rejected by schema validation."""
    # Create an invalid result (missing required field)
    invalid_result = {
        "metadata": {
            "dataset": "test",
            "size": 15,
            "seed": 42
            # Missing 'condition'
        },
        "p_values": [0.05, 0.1, 0.2]
    }
    
    # This should raise an exception or return False
    with pytest.raises(Exception):
        validate_schema(invalid_result, mock_schema_path)
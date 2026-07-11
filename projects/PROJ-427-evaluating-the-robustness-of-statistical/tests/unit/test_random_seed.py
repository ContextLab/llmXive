"""
Unit tests for random seed reproducibility.

This test verifies that setting the seed produces identical results
across multiple runs, specifically checking that injected error counts
are deterministic.
"""
import os
import sys
import tempfile
import shutil
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from random_seed import set_seed
from inject import inject_random_replacement, load_config


def test_seed_determinism_injection_count():
    """
    Test that repeated runs with the same seed produce identical
    injected-error counts.
    """
    # Create a temporary directory for test data
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create a simple test dataset
        np.random.seed(123)  # Use a fixed seed for dataset creation
        data = {
            'col1': np.random.normal(0, 1, 1000),
            'col2': np.random.normal(5, 2, 1000),
            'col3': np.random.choice(['A', 'B', 'C'], 1000)
        }
        df = pd.DataFrame(data)
        test_csv = tmpdir_path / 'test_data.csv'
        df.to_csv(test_csv, index=False)
        
        # Create a minimal config for injection
        config = {
            'error_type': 'replacement',
            'error_rate': 0.1,
            'seed': 42
        }
        config_file = tmpdir_path / 'test_config.yaml'
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        # Run injection twice with the same seed
        results = []
        for i in range(2):
            # Set the seed
            set_seed(42)
            
            # Load the config and data
            df_load = pd.read_csv(test_csv)
            
            # Perform injection
            injected_df = inject_random_replacement(
                df_load, 
                config['error_rate'],
                config['seed']
            )
            
            # Count non-NaN values in original columns (replacement shouldn't introduce NaNs)
            # But we can count how many values changed by comparing to original
            original_values = df_load['col1'].values
            injected_values = injected_df['col1'].values
            changed_count = np.sum(original_values != injected_values)
            results.append(changed_count)
        
        # Assert that both runs produced the same number of changes
        assert results[0] == results[1], f"Injected error counts differ: {results[0]} vs {results[1]}"
        assert results[0] == int(1000 * 0.1), f"Expected ~100 changes, got {results[0]}"


def test_seed_determinism_numpy():
    """
    Test that numpy random operations are deterministic with set_seed.
    """
    set_seed(42)
    arr1 = np.random.rand(5)
    
    set_seed(42)
    arr2 = np.random.rand(5)
    
    np.testing.assert_array_equal(arr1, arr2)


def test_seed_determinism_python_random():
    """
    Test that Python's built-in random is deterministic with set_seed.
    """
    set_seed(42)
    vals1 = [random.random() for _ in range(5)]
    
    set_seed(42)
    vals2 = [random.random() for _ in range(5)]
    
    assert vals1 == vals2

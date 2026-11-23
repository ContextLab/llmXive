import pytest
import os
import sys
import json
import random
from pathlib import Path

# Ensure imports work
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data.generator import generate_synthetic_data
from code.models.train import train_random_forest
from code.main import parse_args, main
import numpy as np

def test_seed_propagation_in_generation():
    """Test that the seed is correctly propagated to data generation."""
    seed = 12345
    stress_type = "drought"
    
    # Generate with seed
    path1 = generate_synthetic_data(n_samples=50, stress_type=stress_type, seed=seed)
    path2 = generate_synthetic_data(n_samples=50, stress_type=stress_type, seed=seed)
    
    # Generate with different seed
    path3 = generate_synthetic_data(n_samples=50, stress_type=stress_type, seed=99999)
    
    # Read data
    import pandas as pd
    df1 = pd.read_parquet(path1)
    df2 = pd.read_parquet(path2)
    df3 = pd.read_parquet(path3)
    
    # Same seed should produce identical data
    assert df1.equals(df2), "Same seed should produce identical data"
    
    # Different seed should produce different data
    # (Allowing for very small probability of collision, but practically impossible)
    assert not df1.equals(df3), "Different seed should produce different data"
    
    # Cleanup
    os.remove(path1)
    os.remove(path2)
    os.remove(path3)

def test_seed_propagation_in_training():
    """Test that the seed is correctly propagated to model training."""
    # Create dummy data
    np.random.seed(42)
    X = np.random.rand(100, 5)
    y = np.random.rand(100)
    
    seed = 54321
    
    # Train twice with same seed
    model1, metrics1 = train_random_forest(X, y, cv=3, seed=seed)
    model2, metrics2 = train_random_forest(X, y, cv=3, seed=seed)
    
    # Train with different seed
    model3, metrics3 = train_random_forest(X, y, cv=3, seed=99999)
    
    # Same seed should produce identical metrics (within float precision)
    assert metrics1['metric_value'] == metrics2['metric_value'], "Same seed should produce identical metrics"
    
    # Different seed should produce different metrics
    # (Again, practically guaranteed)
    assert metrics1['metric_value'] != metrics3['metric_value'], "Different seed should produce different metrics"

def test_main_cli_seed_argument():
    """Test that the main CLI accepts and uses the --seed argument."""
    # This is a basic integration test to ensure the argument is parsed
    # We don't run the full pipeline here to avoid side effects, 
    # but we verify the argument parser works.
    import argparse
    from code.main import parse_args
    
    # Mock sys.argv
    original_argv = sys.argv
    try:
        sys.argv = ['main.py', '--seed', '999', '--stress-type', 'heat', '--n-samples', '10']
        args = parse_args()
        assert args.seed == 999
        assert args.stress_type == 'heat'
        assert args.n_samples == 10
    finally:
        sys.argv = original_argv

def test_reproducibility_end_to_end():
    """Test that running the pipeline twice with the same seed yields identical results."""
    import tempfile
    import shutil
    
    seed = 77777
    stress_type = "drought"
    n_samples = 20
    
    # Create a temporary output directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # First run
        original_argv = sys.argv
        try:
            sys.argv = [
                'main.py', 
                '--seed', str(seed), 
                '--stress-type', stress_type,
                '--n-samples', str(n_samples),
                '--missing-rate', '0.05',
                '--output-dir', tmpdir
            ]
            main()
            
            # Read results
            with open(os.path.join(tmpdir, 'model_metrics.json'), 'r') as f:
                results1 = json.load(f)
        finally:
            sys.argv = original_argv
        
        # Second run
        with tempfile.TemporaryDirectory() as tmpdir2:
            try:
                sys.argv = [
                    'main.py', 
                    '--seed', str(seed), 
                    '--stress-type', stress_type,
                    '--n-samples', str(n_samples),
                    '--missing-rate', '0.05',
                    '--output-dir', tmpdir2
                ]
                main()
                
                # Read results
                with open(os.path.join(tmpdir2, 'model_metrics.json'), 'r') as f:
                    results2 = json.load(f)
            finally:
                sys.argv = original_argv
        
        # Compare results
        # Note: execution_time will differ, so we exclude it
        assert results1['seed_used'] == results2['seed_used']
        assert results1['stress_type'] == results2['stress_type']
        assert results1['n_samples'] == results2['n_samples']
        assert results1['models']['random_forest']['metric_value'] == results2['models']['random_forest']['metric_value']
        assert results1['models']['svm']['metric_value'] == results2['models']['svm']['metric_value']
        assert results1['validation']['permutation_p_value'] == results2['validation']['permutation_p_value']
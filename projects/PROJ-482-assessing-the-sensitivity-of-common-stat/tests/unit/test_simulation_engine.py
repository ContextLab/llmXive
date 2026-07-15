import pytest
import numpy as np
import os
import tempfile
from simulation_engine import run_single_test_replicate, run_adaptive_simulation, clopper_pearson_interval
from config import SimulationConfig

def test_clopper_pearson_interval():
    """Test Clopper-Pearson interval calculation."""
    # Case: 5 successes out of 10 trials
    lower, upper = clopper_pearson_interval(5, 10, alpha=0.05)
    assert 0.1 < lower < 0.5
    assert 0.5 < upper < 0.9
    
    # Case: 0 successes
    lower, upper = clopper_pearson_interval(0, 10)
    assert lower == 0.0
    assert upper > 0.0

def test_run_single_test_replicate_t_test():
    """Test t-test replicate execution."""
    # Create data with known effect (means differ)
    np.random.seed(42)
    group1 = np.random.normal(0, 1, 50)
    group2 = np.random.normal(1, 1, 50)
    
    data = {'group1': group1, 'group2': group2}
    result = run_single_test_replicate("test", "t_test", data, alpha=0.05)
    
    assert 'p_value' in result
    assert 'rejection' in result
    assert 0 <= result['p_value'] <= 1
    # With effect size 1 and n=50, we expect rejection most of the time
    # But this is stochastic, so just check structure
    assert isinstance(result['rejection'], bool)

def test_p_value_clipping_in_adaptive_simulation():
    """Test that p-values are clipped before storage in adaptive simulation."""
    config = SimulationConfig(
        min_replicates=10,
        max_replicates=50,
        target_ci_width=0.5, # Looser for speed
        alpha=0.05
    )
    
    scenario = {
        'n': 20,
        'distribution': 'normal',
        'effect_size': 0.0,
        'test_type': 't_test'
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, 'test_pvalues.csv')
        
        # Run simulation
        result = run_adaptive_simulation(scenario, config, csv_path)
        
        # Check file exists and has content
        assert os.path.exists(csv_path)
        with open(csv_path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) > 1 # Header + data
        
        # Check that p_value_clipped column exists and values are within bounds
        import csv
        reader = csv.DictReader(lines)
        for row in reader:
            p_raw = float(row['p_value_raw'])
            p_clipped = float(row['p_value_clipped'])
            
            # Clipped should be within [1e-10, 1-1e-10]
            epsilon = 1e-10
            assert p_clipped >= epsilon
            assert p_clipped <= (1.0 - epsilon)
            
            # If raw is nan, clipped might be nan, but logic handles it
            if not np.isnan(p_raw):
                assert p_clipped >= epsilon
                assert p_clipped <= (1.0 - epsilon)
import pytest
import os
import tempfile
import csv
from code.config import SimulationConfig
from code.simulation_engine import run_adaptive_simulation

def test_pvalue_streaming_integration():
    """Test that p-values are streamed to CSV during simulation."""
    config = SimulationConfig()
    config.sample_sizes = [10]
    config.distributions = ['normal']
    config.max_replicates = 100
    config.min_replicates = 50
    config.ci_width_threshold = 1.0  # Force early termination for test
    
    with tempfile.TemporaryDirectory() as temp_dir:
        result = run_adaptive_simulation(
            config,
            sample_size=10,
            distribution_type='normal',
            test_type='t_test',
            hypothesis_type='null',
            output_dir=temp_dir
        )
        
        # Verify raw p-values file exists
        pvalues_file = os.path.join(temp_dir, 'raw_pvalues.csv')
        assert os.path.exists(pvalues_file)
        
        # Verify file contents
        with open(pvalues_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) > 0
            
            # Check schema columns
            for row in rows:
                assert 'sample_size' in row
                assert 'distribution_type' in row
                assert 'test_type' in row
                assert 'p_value' in row
                assert 'hypothesis_type' in row
                
                # Verify values match configuration
                assert int(row['sample_size']) == 10
                assert row['distribution_type'] == 'normal'
                assert row['test_type'] == 't_test'
                assert row['hypothesis_type'] == 'null'
                
                # Verify p_value is a valid float
                p_val = float(row['p_value'])
                assert 0.0 <= p_val <= 1.0

def test_pvalue_streaming_multiple_configs():
    """Test streaming with multiple configurations."""
    config = SimulationConfig()
    config.sample_sizes = [10, 20]
    config.distributions = ['normal']
    config.max_replicates = 100
    config.min_replicates = 50
    config.ci_width_threshold = 1.0
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Run two scenarios
        result1 = run_adaptive_simulation(
            config, 10, 'normal', 't_test', 'null', temp_dir
        )
        result2 = run_adaptive_simulation(
            config, 20, 'normal', 't_test', 'null', temp_dir
        )
        
        pvalues_file = os.path.join(temp_dir, 'raw_pvalues.csv')
        assert os.path.exists(pvalues_file)
        
        with open(pvalues_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Should have records from both runs
            assert len(rows) >= 100  # At least min_replicates from each
            
            # Verify both sample sizes are present
            sample_sizes = set(int(r['sample_size']) for r in rows)
            assert 10 in sample_sizes
            assert 20 in sample_sizes

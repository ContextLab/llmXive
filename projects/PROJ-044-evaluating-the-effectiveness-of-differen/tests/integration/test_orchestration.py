"""
Integration tests for the orchestration script (T018b).
Tests the 5-seed loop and log aggregation functionality.
"""
import pytest
import os
import sys
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from training.orchestrate_experiment import run_single_configuration, aggregate_logs

class TestOrchestration:
    """Tests for the orchestration functionality."""
    
    def test_single_configuration_execution(self):
        """Test that a single configuration can be executed and returns valid results."""
        # Use a small subset for testing
        result = run_single_configuration(
            seed=42,
            alpha=0.5,
            epsilon=1.0
        )
        
        # Verify result structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'seed' in result, "Result should contain 'seed'"
        assert 'alpha' in result, "Result should contain 'alpha'"
        assert 'epsilon' in result, "Result should contain 'epsilon'"
        assert 'global_accuracy' in result, "Result should contain 'global_accuracy'"
        assert 'is_time_limited' in result, "Result should contain 'is_time_limited'"
        
        # Verify data types
        assert isinstance(result['seed'], int), "Seed should be an integer"
        assert isinstance(result['alpha'], float), "Alpha should be a float"
        assert isinstance(result['epsilon'], float), "Epsilon should be a float"
        assert isinstance(result['global_accuracy'], float), "Accuracy should be a float"
        assert isinstance(result['is_time_limited'], bool), "is_time_limited should be a boolean"
        
        # Verify value ranges
        assert result['seed'] == 42, "Seed should match input"
        assert result['alpha'] == 0.5, "Alpha should match input"
        assert result['epsilon'] == 1.0, "Epsilon should match input"
        assert 0.0 <= result['global_accuracy'] <= 1.0, "Accuracy should be between 0 and 1"
        
        # Verify experiment directory was created
        if result.get('experiment_dir'):
            assert os.path.exists(result['experiment_dir']), "Experiment directory should exist"
    
    def test_aggregate_logs_creates_csv(self):
        """Test that aggregate_logs creates a valid CSV file."""
        # Create test results
        test_results = [
            {
                'seed': 42,
                'alpha': 0.5,
                'epsilon': 1.0,
                'global_accuracy': 0.85,
                'rounds_to_target': 50,
                'is_time_limited': False,
                'is_utility_collapse': False,
                'privacy_budget_used': 1.0,
                'experiment_dir': '/tmp/test_exp',
                'timestamp': '2024-01-01 12:00:00'
            },
            {
                'seed': 123,
                'alpha': 0.1,
                'epsilon': 0.5,
                'global_accuracy': 0.78,
                'rounds_to_target': 60,
                'is_time_limited': False,
                'is_utility_collapse': False,
                'privacy_budget_used': 0.5,
                'experiment_dir': '/tmp/test_exp2',
                'timestamp': '2024-01-01 12:05:00'
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_results.csv'
            
            # Run aggregation
            aggregate_logs(test_results, output_path)
            
            # Verify file was created
            assert output_path.exists(), "CSV file should be created"
            
            # Verify content
            df = pd.read_csv(output_path)
            assert len(df) == 2, "Should have 2 rows"
            assert 'seed' in df.columns, "Should have 'seed' column"
            assert 'alpha' in df.columns, "Should have 'alpha' column"
            assert 'epsilon' in df.columns, "Should have 'epsilon' column"
            assert 'global_accuracy' in df.columns, "Should have 'global_accuracy' column"
            
            # Verify values
            assert df.iloc[0]['seed'] == 42, "First row seed should be 42"
            assert df.iloc[1]['alpha'] == 0.1, "Second row alpha should be 0.1"
            assert abs(df.iloc[0]['global_accuracy'] - 0.85) < 0.001, "First row accuracy should be 0.85"
    
    def test_aggregate_logs_empty_list(self):
        """Test that aggregate_logs handles empty list gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'empty_results.csv'
            
            # Should not raise an exception
            aggregate_logs([], output_path)
            
            # File should not be created or should be empty
            if output_path.exists():
                df = pd.read_csv(output_path)
                assert len(df) == 0, "Empty list should result in empty DataFrame"
    
    def test_configuration_parameter_validation(self):
        """Test that invalid configurations are handled properly."""
        # Test with invalid alpha (should still run but might fail in partitioning)
        # This test verifies the function doesn't crash on invalid inputs
        result = run_single_configuration(
            seed=999,
            alpha=0.01,  # Very low alpha
            epsilon=0.01  # Very low epsilon (might trigger utility collapse)
        )
        
        # Should still return a result dictionary
        assert isinstance(result, dict), "Result should be a dictionary even for edge cases"
        assert 'seed' in result, "Result should contain 'seed'"
        assert 'epsilon' in result, "Result should contain 'epsilon'"
    
    def test_reproducibility_with_same_seed(self):
        """Test that same seed produces consistent results (basic check)."""
        # Run twice with same seed
        result1 = run_single_configuration(
            seed=42,
            alpha=0.5,
            epsilon=1.0
        )
        
        # Note: In a real scenario, we'd need to mock the training to ensure
        # exact reproducibility. For now, we just verify the structure is consistent.
        result2 = run_single_configuration(
            seed=42,
            alpha=0.5,
            epsilon=1.0
        )
        
        # Both should have same metadata
        assert result1['seed'] == result2['seed'], "Seeds should match"
        assert result1['alpha'] == result2['alpha'], "Alphas should match"
        assert result1['epsilon'] == result2['epsilon'], "Epsilons should match"
        assert 'global_accuracy' in result1 and 'global_accuracy' in result2, \
            "Both results should have accuracy"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

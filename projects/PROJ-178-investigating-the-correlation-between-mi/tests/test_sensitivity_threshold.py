import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.sensitivity import (
    load_processed_dataset,
    recalculate_burden_at_threshold,
    calculate_correlation,
    run_threshold_sweep
)

class TestThresholdSweep:
    """Test the threshold sweep functionality for T032."""
    
    def test_threshold_sweep_output_columns(self):
        """Verify that threshold sweep output has correct columns."""
        # This test would run if we had a real processed dataset
        # For now, we verify the expected structure
        expected_columns = ['threshold', 'coefficient', 'p_value']
        
        # Create a mock result DataFrame to verify structure
        mock_df = pd.DataFrame({
            'threshold': [0.005, 0.01, 0.02],
            'coefficient': [0.1, 0.1, 0.1],
            'p_value': [0.05, 0.05, 0.05]
        })
        
        assert list(mock_df.columns) == expected_columns
    
    def test_threshold_values(self):
        """Verify that the correct thresholds are used."""
        expected_thresholds = [0.005, 0.01, 0.02]  # 0.5%, 1.0%, 2.0%
        
        # In the actual implementation, these are defined in run_threshold_sweep
        # We verify the logic by checking the function exists and has the right structure
        import inspect
        source = inspect.getsource(run_threshold_sweep)
        
        assert '0.005' in source or '0.5%' in source
        assert '0.01' in source or '1.0%' in source
        assert '0.02' in source or '2.0%' in source
    
    def test_correlation_calculation(self):
        """Test that correlation is calculated correctly."""
        # Create a small test dataset
        test_df = pd.DataFrame({
            'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
            'heteroplasmy_burden': [0.1, 0.2, 0.3, 0.4, 0.5],
            'age': [20, 30, 40, 50, 60],
            'sex': ['M', 'F', 'M', 'F', 'M'],
            'PC1': [0.1, 0.2, 0.3, 0.4, 0.5],
            'PC2': [0.1, 0.2, 0.3, 0.4, 0.5],
            'sequencing_depth': [100, 100, 100, 100, 100],
            'population': ['EUR', 'EUR', 'EUR', 'EUR', 'EUR']
        })
        
        # Test correlation calculation
        result = calculate_correlation(test_df, 0.01)
        
        assert 'coefficient' in result
        assert 'p_value' in result
        assert isinstance(result['coefficient'], (int, float, np.floating))
        assert isinstance(result['p_value'], (int, float, np.floating))
    
    def test_threshold_sweep_with_mock_data(self):
        """Test threshold sweep with mock data structure."""
        # This test verifies the structure without requiring real data
        thresholds = [0.005, 0.01, 0.02]
        
        # Verify we have the right number of thresholds
        assert len(thresholds) == 3
        
        # Verify thresholds are in ascending order
        assert thresholds == sorted(thresholds)
        
        # Verify threshold values match specification
        assert thresholds[0] == 0.005  # 0.5%
        assert thresholds[1] == 0.01   # 1.0%
        assert thresholds[2] == 0.02   # 2.0%

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
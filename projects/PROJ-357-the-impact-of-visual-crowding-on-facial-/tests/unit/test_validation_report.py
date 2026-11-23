import os
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats

# Import the module under test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'code'))

from analysis.validation_report import validate_correlation, load_metrics

class TestValidationReport:
    
    @pytest.fixture
    def sample_df(self):
        """Create a mock dataframe with a known positive correlation."""
        # Create data where spatial_frequency_energy increases with flanker_count
        n = 100
        flanker_counts = np.random.choice([3, 5, 7, 9], n)
        # Add noise but maintain a trend
        energy = flanker_counts * 2.5 + np.random.normal(0, 1, n) 
        return pd.DataFrame({
            'file_path': [f"img_{i}.png" for i in range(n)],
            'flanker_count': flanker_counts,
            'spatial_frequency_energy': energy
        })

    def test_validate_correlation_positive(self, sample_df):
        """Test that a positive correlation is detected correctly."""
        result = validate_correlation(sample_df)
        
        assert result['is_significant'] is True
        assert result['status'] == 'PASS'
        assert result['correlation_coefficient'] > 0
        assert result['p_value'] < 0.05
        assert result['direction'] == 'positive'

    def test_validate_correlation_negative(self):
        """Test detection of negative correlation."""
        n = 50
        x = np.arange(n)
        y = -x * 2 + np.random.normal(0, 2, n)
        df = pd.DataFrame({
            'file_path': [f"img_{i}.png" for i in range(n)],
            'flanker_count': x,
            'spatial_frequency_energy': y
        })
        
        result = validate_correlation(df)
        
        assert result['is_significant'] is True
        assert result['status'] == 'PASS'
        assert result['correlation_coefficient'] < 0
        assert result['direction'] == 'negative'

    def test_validate_correlation_no_correlation(self):
        """Test detection of no correlation (random data)."""
        n = 100
        df = pd.DataFrame({
            'file_path': [f"img_{i}.png" for i in range(n)],
            'flanker_count': np.random.randint(1, 10, n),
            'spatial_frequency_energy': np.random.normal(0, 1, n)
        })
        
        result = validate_correlation(df)
        
        # With random data, it might occasionally be significant, but usually not.
        # We check that the function runs and returns valid structure.
        assert 'p_value' in result
        assert 'correlation_coefficient' in result
        assert isinstance(result['is_significant'], bool)

    def test_insufficient_data(self):
        """Test that insufficient data raises an error."""
        df = pd.DataFrame({
            'file_path': ['a.png', 'b.png'],
            'flanker_count': [1, 2],
            'spatial_frequency_energy': [10, 20]
        })
        
        with pytest.raises(ValueError, match="Insufficient data"):
            validate_correlation(df)

    def test_missing_columns(self, sample_df):
        """Test that missing columns raise an error."""
        df_bad = sample_df.drop(columns=['spatial_frequency_energy'])
        
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_correlation(df_bad)
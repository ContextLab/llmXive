import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from loaders import filter_continuous_variables, detect_constant_variables, apply_hygiene_pipeline

class TestVariableTypeEnforcement:
    """Tests for T082: Dataset Variable Type Enforcement"""

    def test_filter_continuous_only_numeric(self):
        """Test that only numeric columns are kept."""
        df = pd.DataFrame({
            'num1': [1.0, 2.0, 3.0, 4.0, 5.0],
            'num2': [10.0, 20.0, 30.0, 40.0, 50.0],
            'cat': ['a', 'b', 'c', 'd', 'e'],
            'bool_col': [True, False, True, False, True]
        })
        
        filtered, kept, dropped = filter_continuous_variables(df)
        
        assert 'num1' in kept
        assert 'num2' in kept
        assert 'cat' not in kept
        assert 'cat' in dropped
        assert len(kept) == 2

    def test_filter_drops_low_variance_numeric(self):
        """Test that numeric columns with few unique values are dropped (likely categorical)."""
        df = pd.DataFrame({
            'continuous': [1.0, 2.3, 3.7, 4.1, 5.9, 6.2, 7.8, 8.4, 9.1, 10.0,
                          11.2, 12.5, 13.3, 14.7, 15.0, 16.1, 17.9, 18.2, 19.5, 20.0],
            'label': [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
        })
        
        filtered, kept, dropped = filter_continuous_variables(df)
        
        # 'label' has only 2 unique values, should be dropped
        assert 'continuous' in kept
        assert 'label' in dropped

    def test_filter_keeps_high_variance_numeric(self):
        """Test that numeric columns with many unique values are kept."""
        n = 50
        df = pd.DataFrame({
            'var1': np.random.randn(n),
            'var2': np.random.randn(n),
            'var3': np.random.randn(n)
        })
        
        filtered, kept, dropped = filter_continuous_variables(df)
        
        assert len(kept) == 3
        assert len(dropped) == 0

    def test_hygiene_pipeline_logs_dropped(self):
        """Test that hygiene pipeline logs dropped variables."""
        df = pd.DataFrame({
            'continuous': [1.0, 2.3, 3.7, 4.1, 5.9, 6.2, 7.8, 8.4, 9.1, 10.0,
                          11.2, 12.5, 13.3, 14.7, 15.0, 16.1, 17.9, 18.2, 19.5, 20.0],
            'categorical': ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
                           'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't']
        })
        
        cleaned, report = apply_hygiene_pipeline(df, 'test_dataset')
        
        assert report['valid'] is True
        assert 'categorical' in report['non_continuous_dropped']
        assert len(report['non_continuous_dropped']) == 1

    def test_constant_variable_detection(self):
        """Test detection of constant variables."""
        df = pd.DataFrame({
            'varied': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
            'constant': [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5]
        })
        
        constant_cols = detect_constant_variables(df)
        
        assert 'constant' in constant_cols
        assert 'varied' not in constant_cols

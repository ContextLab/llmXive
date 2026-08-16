import os
import json
import tempfile
import shutil
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Mock config for testing if necessary, or rely on actual config if set up
# Assuming config is properly set up in the environment or we patch it
# For this unit test, we will test the specific logic functions directly

from data.preprocess import (
    compute_medians,
    impute_missing_values,
    encode_categorical,
    check_sample_count,
    check_zero_variance,
    save_normalization_bounds
)
from sklearn.preprocessing import MinMaxScaler

class TestPreprocessLogic:
    def test_compute_medians(self):
        df = pd.DataFrame({
            'a': [1, 2, 3, 4],
            'b': [10, 20, 30, 40],
            'c': ['x', 'y', 'z', 'w']
        })
        medians = compute_medians(df, ['a', 'b', 'c'])
        assert medians['a'] == 2.5
        assert medians['b'] == 25.0
        assert 'c' not in medians # Non-numeric

    def test_impute_missing_values(self):
        df = pd.DataFrame({
            'a': [1.0, np.nan, 3.0, np.nan],
            'b': [10.0, 20.0, np.nan, 40.0]
        })
        medians = {'a': 2.0, 'b': 25.0}
        df_imputed, count = impute_missing_values(df, medians)
        
        assert df_imputed['a'].isnull().sum() == 0
        assert df_imputed['b'].isnull().sum() == 0
        assert count == 3
        assert df_imputed['a'].iloc[1] == 2.0

    def test_encode_categorical(self):
        df = pd.DataFrame({
            'id': [1, 2, 3, 4],
            'type': ['A', 'B', 'A', 'C']
        })
        df_enc, new_cols = encode_categorical(df, 'type')
        
        assert 'type_A' in df_enc.columns
        assert 'type_B' in df_enc.columns
        assert 'type_C' in df_enc.columns
        assert 'type' not in df_enc.columns
        assert len(new_cols) == 3

    def test_check_sample_count_pass(self):
        df = pd.DataFrame({'a': range(100)})
        # Should not raise
        check_sample_count(df, min_count=50)

    def test_check_sample_count_fail(self):
        df = pd.DataFrame({'a': range(10)})
        with pytest.raises(ValueError):
            check_sample_count(df, min_count=50)

    def test_check_zero_variance(self):
        df = pd.DataFrame({
            'const': [5, 5, 5, 5],
            'var': [1, 2, 3, 4]
        })
        # Create a temp log file path
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            log_path = tmp.name
        
        try:
            dropped = check_zero_variance(df, log_path)
            assert 'const' in dropped
            assert 'var' not in dropped
        finally:
            os.unlink(log_path)

    def test_save_normalization_bounds(self):
        # Create a mock scaler
        data = np.array([[1, 2], [3, 4], [5, 6]])
        scaler = MinMaxScaler()
        scaler.fit(data)
        
        feature_cols = ['f1', 'f2']
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "bounds.json")
            save_normalization_bounds(scaler, feature_cols, output_path)
            
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                bounds = json.load(f)
            
            assert bounds['feature_columns'] == ['f1', 'f2']
            assert 'min_values' in bounds
            assert 'max_values' in bounds
            assert bounds['min_values'] == [1.0, 2.0]
            assert bounds['max_values'] == [5.0, 6.0]

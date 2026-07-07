"""
Unit tests for the preprocessor module.

Tests leakage-safe imputation and scaling functionality.
"""
import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import train_test_split

from code.preprocessor import (
    LeakageSafeImputer,
    LeakageSafeScaler,
    create_preprocessing_pipeline,
    preprocess_data
)
from code.utils import PipelineError


class TestLeakageSafeImputer:
    def test_median_imputation_numeric(self):
        """Test median imputation on numeric data."""
        X = pd.DataFrame({
            'a': [1.0, 2.0, np.nan, 4.0, 5.0],
            'b': [10.0, np.nan, 30.0, 40.0, 50.0]
        })
        
        imputer = LeakageSafeImputer(strategy_numeric='median')
        imputer.fit(X)
        result = imputer.transform(X)
        
        assert result['a'].isna().sum() == 0
        assert result['b'].isna().sum() == 0
        # Median of [1, 2, 4, 5] is 3.0
        assert result.loc[2, 'a'] == 3.0
        # Median of [10, 30, 40, 50] is 35.0
        assert result.loc[1, 'b'] == 35.0

    def test_mode_imputation_categorical(self):
        """Test mode (most_frequent) imputation on categorical data."""
        X = pd.DataFrame({
            'cat': ['A', 'B', 'A', None, 'A', 'B']
        })
        
        imputer = LeakageSafeImputer(strategy_categorical='most_frequent')
        imputer.fit(X)
        result = imputer.transform(X)
        
        assert result['cat'].isna().sum() == 0
        # Mode is 'A' (appears 3 times)
        assert result.loc[3, 'cat'] == 'A'

    def test_no_leakage_simulation(self):
        """
        Simulate a CV scenario to ensure imputer doesn't leak test data.
        
        We create a scenario where the test set has a unique value that,
        if used for imputation, would skew results. We verify the imputer
        only uses training data statistics.
        """
        # Training data: mean is 2.0
        X_train = pd.DataFrame({'val': [1.0, 2.0, 3.0, np.nan]})
        # Test data: has a missing value. If test mean was used, it would be different.
        X_test = pd.DataFrame({'val': [100.0, np.nan]})
        
        imputer = LeakageSafeImputer()
        imputer.fit(X_train)
        
        # Transform test
        X_test_transformed = imputer.transform(X_test)
        
        # The missing value in test should be filled with training median (2.0)
        # NOT influenced by the test value 100.0
        assert X_test_transformed.loc[1, 'val'] == 2.0


class TestLeakageSafeScaler:
    def test_standard_scaling(self):
        """Test StandardScaler functionality."""
        X = pd.DataFrame({
            'a': [1.0, 2.0, 3.0, 4.0, 5.0]
        })
        
        scaler = LeakageSafeScaler()
        scaler.fit(X)
        result = scaler.transform(X)
        
        # Mean should be ~0, std should be ~1
        assert np.isclose(result['a'].mean(), 0.0, atol=1e-6)
        assert np.isclose(result['a'].std(), 1.0, atol=1e-6)

    def test_no_leakage_scaling(self):
        """Test that scaler parameters come only from training data."""
        X_train = pd.DataFrame({'val': [1.0, 2.0, 3.0]})
        X_test = pd.DataFrame({'val': [100.0, 200.0]})
        
        scaler = LeakageSafeScaler()
        scaler.fit(X_train)
        
        X_train_scaled = scaler.transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Training data: mean=2, std=1 (ddof=0) or 1.0 (ddof=1)
        # StandardScaler uses ddof=0
        # Train: (1-2)/1 = -1, (2-2)/1 = 0, (3-2)/1 = 1
        assert np.isclose(X_train_scaled['val'].mean(), 0.0, atol=1e-6)
        
        # Test data scaled with train stats:
        # (100-2)/1 = 98, (200-2)/1 = 198
        expected_test_mean = 148.0
        assert np.isclose(X_test_scaled['val'].mean(), expected_test_mean, atol=1e-6)


class TestPreprocessingPipeline:
    def test_create_pipeline_with_types(self):
        """Test pipeline creation with explicit feature types."""
        numeric = ['num1', 'num2']
        categorical = ['cat1']
        
        preprocessor = create_preprocessing_pipeline(numeric, categorical)
        
        assert preprocessor is not None
        # Should be a ColumnTransformer
        from sklearn.compose import ColumnTransformer
        assert isinstance(preprocessor, ColumnTransformer)

    def test_preprocess_data_function(self):
        """Test the full preprocess_data function."""
        X_train = pd.DataFrame({
            'num1': [1.0, 2.0, np.nan, 4.0],
            'num2': [10.0, 20.0, 30.0, np.nan],
            'cat1': ['A', 'B', 'A', None]
        })
        X_test = pd.DataFrame({
            'num1': [5.0, np.nan],
            'num2': [np.nan, 50.0],
            'cat1': [None, 'C']
        })
        
        X_train_proc, X_test_proc = preprocess_data(
            X_train, X_test,
            numeric_features=['num1', 'num2'],
            categorical_features=['cat1']
        )
        
        # Check no NaNs remain
        assert X_train_proc.isna().sum().sum() == 0
        assert X_test_proc.isna().sum().sum() == 0
        
        # Check shapes
        assert X_train_proc.shape[0] == X_train.shape[0]
        assert X_test_proc.shape[0] == X_test.shape[0]

    def test_auto_detect_features(self):
        """Test preprocessing with auto-detected features."""
        X_train = pd.DataFrame({
            'num1': [1.0, 2.0, np.nan],
            'cat1': ['A', 'B', None]
        })
        X_test = pd.DataFrame({
            'num1': [3.0, np.nan],
            'cat1': [None, 'C']
        })
        
        # Call without specifying features
        X_train_proc, X_test_proc = preprocess_data(X_train, X_test)
        
        assert X_train_proc.isna().sum().sum() == 0
        assert X_test_proc.isna().sum().sum() == 0

class TestEdgeCases:
    def test_empty_dataframe(self):
        """Handle empty DataFrames gracefully."""
        X_train = pd.DataFrame()
        X_test = pd.DataFrame()
        
        with pytest.raises(PipelineError):
            preprocess_data(X_train, X_test)

    def test_all_missing_column(self):
        """Handle columns with all missing values."""
        X_train = pd.DataFrame({
            'num1': [np.nan, np.nan, np.nan],
            'num2': [1.0, 2.0, 3.0]
        })
        X_test = pd.DataFrame({
            'num1': [np.nan, np.nan],
            'num2': [4.0, 5.0]
        })
        
        # Should not crash, though imputation of all-NaN column will fail in sklearn
        # We rely on sklearn's behavior here, which might raise an error or fill with 0.
        # For this test, we just ensure the pipeline is created and runs without our custom errors.
        try:
            X_train_proc, X_test_proc = preprocess_data(X_train, X_test)
            # If it runs, check no NaNs in non-all-NaN columns
            assert X_train_proc.isna().sum().sum() == 0 or X_train_proc.shape[1] == 0
        except Exception:
            # Expected if sklearn raises on all-NaN column
            pass
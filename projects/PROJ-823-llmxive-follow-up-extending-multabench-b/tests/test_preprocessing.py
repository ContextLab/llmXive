"""
Tests for preprocessing edge case handling (T016).
Tests zero-variance column detection and missing field handling.
"""
import pytest
import pandas as pd
import numpy as np
from embeddings.preprocessing import (
    detect_zero_variance_columns,
    detect_missing_fields,
    handle_zero_variance_columns,
    handle_missing_fields,
    validate_dataset_fields,
    preprocess_dataset_for_embedding
)


class TestZeroVarianceDetection:
    """Tests for zero-variance column detection."""
    
    def test_detect_zero_variance_columns(self):
        """Test detection of zero-variance columns."""
        df = pd.DataFrame({
            'constant_col': [5, 5, 5, 5],
            'varying_col': [1, 2, 3, 4],
            'another_constant': [0.0, 0.0, 0.0, 0.0],
            'normal_col': [10, 20, 30, 40]
        })
        
        zero_var = detect_zero_variance_columns(df)
        
        assert 'constant_col' in zero_var
        assert 'another_constant' in zero_var
        assert 'varying_col' not in zero_var
        assert 'normal_col' not in zero_var
        assert len(zero_var) == 2
        
    def test_detect_zero_variance_empty_df(self):
        """Test detection with empty DataFrame."""
        df = pd.DataFrame()
        zero_var = detect_zero_variance_columns(df)
        assert zero_var == []
        
    def test_detect_zero_variance_none_df(self):
        """Test detection with None DataFrame."""
        zero_var = detect_zero_variance_columns(None)
        assert zero_var == []
        
    def test_detect_zero_variance_single_value(self):
        """Test detection with single-row DataFrame."""
        df = pd.DataFrame({
            'single_col': [42],
            'other_col': [100]
        })
        zero_var = detect_zero_variance_columns(df)
        # Single value has zero variance (nunique() = 1)
        assert 'single_col' in zero_var
        assert 'other_col' in zero_var


class TestMissingFieldsDetection:
    """Tests for missing field detection."""
    
    def test_detect_missing_fields(self):
        """Test detection of missing required fields."""
        row = {
            'image': 'path/to/image.jpg',
            'text': 'Some text'
        }
        required = ['image', 'text', 'label']
        
        missing = detect_missing_fields(row, required)
        
        assert 'label' in missing
        assert 'image' not in missing
        assert 'text' not in missing
        assert len(missing) == 1
        
    def test_detect_missing_fields_all_present(self):
        """Test when all required fields are present."""
        row = {
            'image': 'path.jpg',
            'text': 'text',
            'label': 1
        }
        required = ['image', 'text', 'label']
        
        missing = detect_missing_fields(row, required)
        assert missing == []
        
    def test_detect_missing_fields_none_value(self):
        """Test when field exists but is None."""
        row = {
            'image': None,
            'text': 'text'
        }
        required = ['image', 'text']
        
        missing = detect_missing_fields(row, required)
        assert 'image' in missing


class TestZeroVarianceHandling:
    """Tests for zero-variance column handling strategies."""
    
    def test_handle_zero_variance_drop(self):
        """Test dropping zero-variance columns."""
        df = pd.DataFrame({
            'constant': [5, 5, 5],
            'varying': [1, 2, 3],
            'another_const': [0, 0, 0]
        })
        
        df_processed, handled = handle_zero_variance_columns(df, strategy='drop')
        
        assert 'constant' not in df_processed.columns
        assert 'another_const' not in df_processed.columns
        assert 'varying' in df_processed.columns
        assert len(handled) == 2
        
    def test_handle_zero_variance_impute(self):
        """Test imputing zero-variance columns with constant value."""
        df = pd.DataFrame({
            'constant': [5, 5, 5],
            'varying': [1, 2, 3]
        })
        
        df_processed, handled = handle_zero_variance_columns(
            df, 
            strategy='impute',
            constant_value=999
        )
        
        assert 'constant' in df_processed.columns
        assert all(df_processed['constant'] == 999)
        assert len(handled) == 1
        
    def test_handle_zero_variance_impute_mean(self):
        """Test imputing with mean when no constant provided."""
        df = pd.DataFrame({
            'constant': [5.0, 5.0, 5.0],
            'varying': [1, 2, 3]
        })
        
        df_processed, handled = handle_zero_variance_columns(df, strategy='impute')
        
        assert 'constant' in df_processed.columns
        assert all(df_processed['constant'] == 5.0)
        
    def test_handle_zero_variance_none_df(self):
        """Test handling with None DataFrame."""
        df_processed, handled = handle_zero_variance_columns(None, strategy='drop')
        assert df_processed is None
        assert handled == []


class TestMissingFieldsHandling:
    """Tests for missing field handling strategies."""
    
    def test_handle_missing_fields_skip(self):
        """Test skipping rows with missing fields."""
        row = {'image': 'path.jpg'}
        required = ['image', 'text']
        
        processed, should_skip = handle_missing_fields(
            row, 
            required, 
            strategy='skip'
        )
        
        assert should_skip is True
        assert processed == row
        
    def test_handle_missing_fields_impute(self):
        """Test imputing missing fields."""
        row = {'image': 'path.jpg'}
        required = ['image', 'text']
        
        processed, should_skip = handle_missing_fields(
            row, 
            required, 
            strategy='impute',
            impute_value='N/A'
        )
        
        assert should_skip is False
        assert processed['text'] == 'N/A'
        assert processed['image'] == 'path.jpg'
        
    def test_handle_missing_fields_all_present(self):
        """Test when all fields present."""
        row = {'image': 'path.jpg', 'text': 'text'}
        required = ['image', 'text']
        
        processed, should_skip = handle_missing_fields(row, required, strategy='skip')
        
        assert should_skip is False
        assert processed == row


class TestDatasetValidation:
    """Tests for complete dataset validation."""
    
    def test_validate_dataset_valid(self):
        """Test validation of a valid dataset."""
        dataset = {
            'data': pd.DataFrame({
                'image': ['img1.jpg', 'img2.jpg'],
                'text': ['text1', 'text2'],
                'value': [1, 2]
            })
        }
        required = ['image', 'text']
        
        is_valid, details = validate_dataset_fields(dataset, required)
        
        assert is_valid is True
        assert len(details['missing_fields']) == 0
        assert len(details['zero_variance_cols']) == 0
        
    def test_validate_dataset_missing_fields(self):
        """Test validation with missing required fields."""
        dataset = {
            'data': pd.DataFrame({
                'image': ['img1.jpg', 'img2.jpg']
            })
        }
        required = ['image', 'text']
        
        is_valid, details = validate_dataset_fields(dataset, required)
        
        assert is_valid is False
        assert 'text' in details['missing_fields']
        
    def test_validate_dataset_zero_variance(self):
        """Test validation with zero-variance columns."""
        dataset = {
            'data': pd.DataFrame({
                'image': ['img1.jpg', 'img2.jpg'],
                'text': ['text1', 'text2'],
                'constant': [5, 5]
            })
        }
        required = ['image', 'text']
        
        is_valid, details = validate_dataset_fields(dataset, required)
        
        assert is_valid is True  # Fields present, but warning about variance
        assert 'constant' in details['zero_variance_cols']


class TestPreprocessDataset:
    """Tests for complete dataset preprocessing."""
    
    def test_preprocess_drop_zero_variance(self):
        """Test preprocessing with drop strategy."""
        dataset = {
            'data': pd.DataFrame({
                'image': ['img1.jpg', 'img2.jpg'],
                'text': ['text1', 'text2'],
                'constant': [5, 5]
            })
        }
        required = ['image', 'text']
        
        processed, details = preprocess_dataset_for_embedding(
            dataset, 
            required, 
            zero_var_strategy='drop'
        )
        
        assert processed is not None
        assert 'constant' not in processed['data'].columns
        assert len(details['handled_zero_variance']) == 1
        
    def test_preprocess_skip_missing_fields(self):
        """Test preprocessing when missing fields and strategy is skip."""
        dataset = {
            'data': pd.DataFrame({
                'image': ['img1.jpg', 'img2.jpg']
            })
        }
        required = ['image', 'text']
        
        processed, details = preprocess_dataset_for_embedding(
            dataset, 
            required, 
            missing_field_strategy='skip'
        )
        
        assert processed is None  # Cannot process, missing required field
        assert len(details['validation']['missing_fields']) == 1
        
    def test_preprocess_impute_missing_fields(self):
        """Test preprocessing when imputing missing fields."""
        dataset = {
            'data': pd.DataFrame({
                'image': ['img1.jpg', 'img2.jpg']
            })
        }
        required = ['image', 'text']
        
        processed, details = preprocess_dataset_for_embedding(
            dataset, 
            required, 
            missing_field_strategy='impute'
        )
        
        assert processed is not None
        # Note: Actual imputation happens row-by-row during embedding generation

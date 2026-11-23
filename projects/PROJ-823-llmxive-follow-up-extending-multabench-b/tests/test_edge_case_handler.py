import pytest
import pandas as pd
import numpy as np
from embeddings.edge_case_handler import (
    EdgeCaseHandler,
    detect_zero_variance_columns,
    detect_missing_fields,
    handle_zero_variance_columns,
    handle_missing_fields,
    preprocess_dataset_for_edge_cases
)

class TestEdgeCaseHandler:
    """Tests for the EdgeCaseHandler class and convenience functions."""

    @pytest.fixture
    def sample_df_with_zero_var(self):
        """Create a sample DataFrame with zero-variance columns."""
        return pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'constant_col': [5.0, 5.0, 5.0, 5.0, 5.0],
            'variable_col': [1.0, 2.0, 3.0, 4.0, 5.0],
            'image_path': ['img1.jpg', 'img2.jpg', 'img3.jpg', 'img4.jpg', 'img5.jpg'],
            'text_content': ['text1', 'text2', 'text3', 'text4', 'text5']
        })

    @pytest.fixture
    def sample_df_with_missing(self):
        """Create a sample DataFrame with missing values."""
        return pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'value': [1.0, 2.0, 3.0, 4.0, 5.0],
            'image_path': ['img1.jpg', None, 'img3.jpg', None, 'img5.jpg'],
            'text_content': ['text1', 'text2', None, 'text4', 'text5']
        })

    def test_detect_zero_variance_columns(self, sample_df_with_zero_var):
        """Test detection of zero-variance columns."""
        zero_var_cols = detect_zero_variance_columns(sample_df_with_zero_var)
        assert 'constant_col' in zero_var_cols
        assert 'variable_col' not in zero_var_cols
        assert len(zero_var_cols) == 1

    def test_detect_missing_fields(self, sample_df_with_missing):
        """Test detection of missing fields."""
        required_fields = ['image_path', 'text_content', 'nonexistent_field']
        missing_info = detect_missing_fields(sample_df_with_missing, required_fields)

        assert 'nonexistent_field' in missing_info['missing_fields']
        assert missing_info['missing_values']['image_path'] == 2
        assert missing_info['missing_values']['text_content'] == 1

    def test_handle_zero_variance_skip(self, sample_df_with_zero_var):
        """Test handling zero-variance columns by skipping."""
        handler = EdgeCaseHandler(zero_var_strategy="skip")
        zero_var_cols = ['constant_col']

        df_processed, metadata = handler.handle_zero_variance_columns(
            sample_df_with_zero_var, zero_var_cols
        )

        assert 'constant_col' not in df_processed.columns
        assert 'variable_col' in df_processed.columns
        assert metadata['action'] == 'skip'

    def test_handle_zero_variance_impute(self, sample_df_with_zero_var):
        """Test handling zero-variance columns by imputation."""
        handler = EdgeCaseHandler(zero_var_strategy="impute_constant")
        zero_var_cols = ['constant_col']

        df_processed, metadata = handler.handle_zero_variance_columns(
            sample_df_with_zero_var, zero_var_cols, constant_value=99.0
        )

        assert 'constant_col' in df_processed.columns
        assert all(df_processed['constant_col'] == 99.0)
        assert metadata['action'] == 'impute_constant'

    def test_handle_missing_skip(self, sample_df_with_missing):
        """Test handling missing fields by skipping rows."""
        handler = EdgeCaseHandler(missing_strategy="skip")
        missing_info = detect_missing_fields(
            sample_df_with_missing,
            ['image_path', 'text_content']
        )

        df_processed, metadata = handler.handle_missing_fields(
            sample_df_with_missing, missing_info
        )

        # Should drop rows 2 and 4 (0-indexed: 1 and 3) which have missing values
        assert len(df_processed) == 3
        assert metadata['rows_dropped'] == 2

    def test_handle_missing_impute(self, sample_df_with_missing):
        """Test handling missing fields by imputation."""
        handler = EdgeCaseHandler(missing_strategy="impute_constant")
        missing_info = detect_missing_fields(
            sample_df_with_missing,
            ['image_path', 'text_content']
        )

        df_processed, metadata = handler.handle_missing_fields(
            sample_df_with_missing, missing_info,
            image_fill="MISSING_IMG", text_fill="MISSING_TXT"
        )

        assert len(df_processed) == 5
        assert df_processed.loc[1, 'image_path'] == "MISSING_IMG"
        assert df_processed.loc[2, 'text_content'] == "MISSING_TXT"
        assert metadata['action'] == 'impute_constant'

    def test_handle_missing_error(self, sample_df_with_missing):
        """Test handling missing fields by raising error."""
        handler = EdgeCaseHandler(missing_strategy="error")
        missing_info = detect_missing_fields(
            sample_df_with_missing,
            ['image_path', 'text_content']
        )

        with pytest.raises(ValueError, match="Missing required data detected"):
            handler.handle_missing_fields(sample_df_with_missing, missing_info)

    def test_preprocess_dataset_for_edge_cases(self, sample_df_with_zero_var, sample_df_with_missing):
        """Test the full preprocessing pipeline."""
        # Test with zero-variance data
        df_processed, metadata = preprocess_dataset_for_edge_cases(
            sample_df_with_zero_var,
            required_fields=['image_path', 'text_content'],
            zero_var_strategy='skip',
            missing_strategy='impute_constant'
        )

        assert 'constant_col' not in df_processed.columns
        assert metadata['final_row_count'] == 5
        assert metadata['final_column_count'] == 4  # Original 5 minus 1 dropped

    def test_preprocess_with_missing_data(self, sample_df_with_missing):
        """Test preprocessing with missing data."""
        df_processed, metadata = preprocess_dataset_for_edge_cases(
            sample_df_with_missing,
            required_fields=['image_path', 'text_content'],
            zero_var_strategy='impute_constant',
            missing_strategy='skip'
        )

        assert len(df_processed) == 3
        assert metadata['missing_handling']['rows_dropped'] == 2

    def test_convenience_functions(self, sample_df_with_zero_var):
        """Test that convenience functions work correctly."""
        # Test detect_zero_variance_columns
        cols = detect_zero_variance_columns(sample_df_with_zero_var)
        assert 'constant_col' in cols

        # Test handle_zero_variance_columns
        df_new, meta = handle_zero_variance_columns(
            sample_df_with_zero_var, ['constant_col'], strategy='skip'
        )
        assert 'constant_col' not in df_new.columns
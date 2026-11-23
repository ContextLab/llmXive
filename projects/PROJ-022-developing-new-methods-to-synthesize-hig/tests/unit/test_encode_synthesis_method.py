"""
Unit tests for categorical encoding of synthesis method (T023).

Tests FR-008: Add categorical encoding for 'synthesis method' in the feature matrix.
"""
import os
import sys
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from features.encode_synthesis_method import (
    load_feature_matrix_or_standardized_data,
    encode_synthesis_method,
    save_encoded_features,
    validate_encoding,
    main,
    SYNTHESIS_METHOD_COLUMN
)
from utils.errors import DataInsufficientError


class TestLoadFeatureMatrixOrStandardizedData:
    """Tests for the data loading function."""
    
    def test_load_feature_matrix_with_synthesis_method(self, tmp_path):
        """Test loading feature matrix that contains synthesis method column."""
        # Create test data
        test_data = pd.DataFrame({
            'polymer_id': [1, 2, 3],
            'synthesis_method': ['solution_casting', 'phase_inversion', 'electrospinning'],
            'permeability': [100, 200, 150]
        })
        
        feature_matrix_path = tmp_path / "feature_matrix.csv"
        test_data.to_csv(feature_matrix_path, index=False)
        
        with patch('features.encode_synthesis_method.project_root', tmp_path), \
             patch('features.encode_synthesis_method.FEATURE_MATRIX_PATH', 'feature_matrix.csv'):
            df = load_feature_matrix_or_standardized_data()
            
        assert len(df) == 3
        assert SYNTHESIS_METHOD_COLUMN in df.columns
        assert df['synthesis_method'].tolist() == ['solution_casting', 'phase_inversion', 'electrospinning']
    
    def test_load_standardized_data_when_feature_matrix_missing(self, tmp_path):
        """Test falling back to standardized data when feature matrix is missing."""
        # Create standardized data
        test_data = pd.DataFrame({
            'polymer_id': [1, 2, 3],
            'synthesis_method': ['solution_casting', 'phase_inversion', 'electrospinning'],
            'permeability': [100, 200, 150]
        })
        
        standardized_path = tmp_path / "standardized_polymers.csv"
        test_data.to_csv(standardized_path, index=False)
        
        with patch('features.encode_synthesis_method.project_root', tmp_path), \
             patch('features.encode_synthesis_method.FEATURE_MATRIX_PATH', 'nonexistent.csv'), \
             patch('features.encode_synthesis_method.STANDARDIZED_DATA_PATH', 'standardized_polymers.csv'):
            df = load_feature_matrix_or_standardized_data()
            
        assert len(df) == 3
        assert SYNTHESIS_METHOD_COLUMN in df.columns
    
    def test_raises_error_when_no_data_available(self, tmp_path):
        """Test that DataInsufficientError is raised when no data files exist."""
        with patch('features.encode_synthesis_method.project_root', tmp_path):
            with pytest.raises(DataInsufficientError):
                load_feature_matrix_or_standardized_data()
    
    def test_raises_error_when_missing_synthesis_column(self, tmp_path):
        """Test that DataInsufficientError is raised when synthesis method column is missing."""
        # Create data without synthesis method column
        test_data = pd.DataFrame({
            'polymer_id': [1, 2, 3],
            'permeability': [100, 200, 150]
        })
        
        standardized_path = tmp_path / "standardized_polymers.csv"
        test_data.to_csv(standardized_path, index=False)
        
        with patch('features.encode_synthesis_method.project_root', tmp_path), \
             patch('features.encode_synthesis_method.FEATURE_MATRIX_PATH', 'nonexistent.csv'), \
             patch('features.encode_synthesis_method.STANDARDIZED_DATA_PATH', 'standardized_polymers.csv'):
            with pytest.raises(DataInsufficientError):
                load_feature_matrix_or_standardized_data()


class TestEncodeSynthesisMethod:
    """Tests for the encoding function."""
    
    def test_encode_single_method(self):
        """Test encoding when all samples have the same synthesis method."""
        df = pd.DataFrame({
            'polymer_id': [1, 2, 3],
            'synthesis_method': ['solution_casting', 'solution_casting', 'solution_casting'],
            'permeability': [100, 200, 150]
        })
        
        df_encoded, encoding_info = encode_synthesis_method(df)
        
        assert 'synthesis_method_solution_casting' in df_encoded.columns
        assert df_encoded['synthesis_method_solution_casting'].sum() == 3
        assert len(encoding_info['categories']) == 1
    
    def test_encode_multiple_methods(self):
        """Test encoding with multiple distinct synthesis methods."""
        df = pd.DataFrame({
            'polymer_id': [1, 2, 3, 4],
            'synthesis_method': ['solution_casting', 'phase_inversion', 'electrospinning', 'solution_casting'],
            'permeability': [100, 200, 150, 180]
        })
        
        df_encoded, encoding_info = encode_synthesis_method(df)
        
        expected_methods = ['solution_casting', 'phase_inversion', 'electrospinning']
        assert len(encoding_info['categories']) == 3
        assert set(encoding_info['categories']) == set(expected_methods)
        
        # Check that each row has exactly one 1 in the encoded columns
        encoded_cols = [col for col in df_encoded.columns if col.startswith('synthesis_method_')]
        row_sums = df_encoded[encoded_cols].sum(axis=1)
        assert all(row_sums == 1)
    
    def test_handle_missing_values(self):
        """Test that missing values are handled as 'Unknown' category."""
        df = pd.DataFrame({
            'polymer_id': [1, 2, 3],
            'synthesis_method': ['solution_casting', None, 'electrospinning'],
            'permeability': [100, 200, 150]
        })
        
        df_encoded, encoding_info = encode_synthesis_method(df)
        
        assert 'synthesis_method_Unknown' in df_encoded.columns
        assert df_encoded['synthesis_method_Unknown'].sum() == 1
    
    def test_all_missing_values_raises_error(self):
        """Test that all missing values raises DataInsufficientError."""
        df = pd.DataFrame({
            'polymer_id': [1, 2, 3],
            'synthesis_method': [None, None, None],
            'permeability': [100, 200, 150]
        })
        
        with pytest.raises(DataInsufficientError):
            encode_synthesis_method(df)
    
    def test_empty_dataframe_raises_error(self):
        """Test that empty DataFrame raises DataInsufficientError."""
        df = pd.DataFrame(columns=['polymer_id', 'synthesis_method', 'permeability'])
        
        with pytest.raises(DataInsufficientError):
            encode_synthesis_method(df)
    
    def test_missing_column_raises_error(self):
        """Test that missing synthesis method column raises DataInsufficientError."""
        df = pd.DataFrame({
            'polymer_id': [1, 2, 3],
            'permeability': [100, 200, 150]
        })
        
        with pytest.raises(DataInsufficientError):
            encode_synthesis_method(df)


class TestValidateEncoding:
    """Tests for the validation function."""
    
    def test_valid_encoding(self):
        """Test validation passes for correctly encoded data."""
        original_df = pd.DataFrame({
            'polymer_id': [1, 2, 3],
            'synthesis_method': ['solution_casting', 'phase_inversion', 'electrospinning'],
            'permeability': [100, 200, 150]
        })
        
        df_encoded = pd.DataFrame({
            'polymer_id': [1, 2, 3],
            'permeability': [100, 200, 150],
            'synthesis_method_solution_casting': [1, 0, 0],
            'synthesis_method_phase_inversion': [0, 1, 0],
            'synthesis_method_electrospinning': [0, 0, 1]
        })
        
        assert validate_encoding(df_encoded, original_df) is True
    
    def test_missing_original_columns(self):
        """Test validation fails when original columns are missing."""
        original_df = pd.DataFrame({
            'polymer_id': [1, 2, 3],
            'synthesis_method': ['solution_casting', 'phase_inversion', 'electrospinning'],
            'permeability': [100, 200, 150]
        })
        
        df_encoded = pd.DataFrame({
            'polymer_id': [1, 2, 3],
            # Missing 'permeability' column
            'synthesis_method_solution_casting': [1, 0, 0],
            'synthesis_method_phase_inversion': [0, 1, 0],
            'synthesis_method_electrospinning': [0, 0, 1]
        })
        
        assert validate_encoding(df_encoded, original_df) is False
    
    def test_no_encoded_columns(self):
        """Test validation fails when no encoded columns exist."""
        original_df = pd.DataFrame({
            'polymer_id': [1, 2, 3],
            'synthesis_method': ['solution_casting', 'phase_inversion', 'electrospinning'],
            'permeability': [100, 200, 150]
        })
        
        df_encoded = pd.DataFrame({
            'polymer_id': [1, 2, 3],
            'permeability': [100, 200, 150]
            # No encoded synthesis method columns
        })
        
        assert validate_encoding(df_encoded, original_df) is False


class TestSaveEncodedFeatures:
    """Tests for the save function."""
    
    def test_save_encoded_features_creates_files(self, tmp_path):
        """Test that save function creates both CSV and JSON files."""
        df_encoded = pd.DataFrame({
            'polymer_id': [1, 2, 3],
            'synthesis_method_solution_casting': [1, 0, 0],
            'synthesis_method_phase_inversion': [0, 1, 0]
        })
        
        encoding_info = {
            'categories': ['solution_casting', 'phase_inversion'],
            'encoded_columns': ['synthesis_method_solution_casting', 'synthesis_method_phase_inversion']
        }
        
        # Mock the project root
        with patch('features.encode_synthesis_method.project_root', tmp_path), \
             patch('features.encode_synthesis_method.ENCODED_FEATURE_MATRIX_PATH', 'feature_matrix_encoded.csv'), \
             patch('features.encode_synthesis_method.ENCODING_MAPPING_PATH', 'synthesis_method_encoding.json'):
            save_encoded_features(df_encoded, encoding_info)
        
        # Check that files were created
        csv_path = tmp_path / 'feature_matrix_encoded.csv'
        json_path = tmp_path / 'synthesis_method_encoding.json'
        
        assert csv_path.exists()
        assert json_path.exists()
        
        # Verify content
        saved_df = pd.read_csv(csv_path)
        assert len(saved_df) == 3
        
        with open(json_path, 'r') as f:
            saved_info = json.load(f)
        assert saved_info == encoding_info

class TestMainFunction:
    """Tests for the main entry point."""
    
    def test_main_success(self, tmp_path, caplog):
        """Test main function completes successfully with valid data."""
        # Create test data
        test_data = pd.DataFrame({
            'polymer_id': [1, 2, 3],
            'synthesis_method': ['solution_casting', 'phase_inversion', 'electrospinning'],
            'permeability': [100, 200, 150]
        })
        
        standardized_path = tmp_path / 'standardized_polymers.csv'
        test_data.to_csv(standardized_path, index=False)
        
        # Mock paths
        with patch('features.encode_synthesis_method.project_root', tmp_path), \
             patch('features.encode_synthesis_method.FEATURE_MATRIX_PATH', 'nonexistent.csv'), \
             patch('features.encode_synthesis_method.STANDARDIZED_DATA_PATH', 'standardized_polymers.csv'), \
             patch('features.encode_synthesis_method.ENCODED_FEATURE_MATRIX_PATH', 'feature_matrix_encoded.csv'), \
             patch('features.encode_synthesis_method.ENCODING_MAPPING_PATH', 'synthesis_method_encoding.json'):
            result = main()
        
        assert result == 0
        
        # Check output files were created
        assert (tmp_path / 'feature_matrix_encoded.csv').exists()
        assert (tmp_path / 'synthesis_method_encoding.json').exists()
    
    def test_main_with_data_insufficient_error(self, tmp_path, caplog):
        """Test main function returns error code when data is insufficient."""
        with patch('features.encode_synthesis_method.project_root', tmp_path):
            result = main()
        
        assert result == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
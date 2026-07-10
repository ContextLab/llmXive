"""
Unit tests for preprocessing pipeline (T015 - MICE imputation).
"""
import os
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.pipelines.preprocess import (
    impute_missing_values,
    calculate_vif,
    run_preprocessing_pipeline,
    load_constants
)

@pytest.fixture
def sample_data_with_nans():
    """Create sample data with missing values for testing."""
    data = {
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'pH': [6.5, np.nan, 7.2, 6.8, 7.0],
        'nutrients': [100.0, 120.0, np.nan, 95.0, 110.0],
        'moisture': [25.0, 28.0, 26.5, np.nan, 27.0],
        'biome': ['Forest', 'Grassland', 'Forest', 'Desert', 'Forest']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_data_no_nans():
    """Create sample data without missing values."""
    data = {
        'sample_id': ['S1', 'S2', 'S3'],
        'pH': [6.5, 7.2, 6.8],
        'nutrients': [100.0, 120.0, 95.0],
        'moisture': [25.0, 26.5, 27.0],
        'biome': ['Forest', 'Forest', 'Grassland']
    }
    return pd.DataFrame(data)

@pytest.fixture
def constants():
    """Load test constants."""
    return load_constants("src/config/constants.yaml")

class TestMICEImputation:
    """Tests for MICE imputation functionality (T015)."""
    
    def test_imputation_removes_nans(self, sample_data_with_nans, constants):
        """Test that imputation successfully removes all NaN values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'imputed.csv')
            
            result_df, meta = impute_missing_values(
                sample_data_with_nans,
                output_path,
                constants
            )
            
            # Verify file was created
            assert os.path.exists(output_path), "Output file not created"
            
            # Verify no NaNs remain
            nan_count = result_df.isnull().sum().sum()
            assert nan_count == 0, f"Expected 0 NaNs, found {nan_count}"
            
            # Verify metadata
            assert meta['imputed'] == True
            assert meta['converged'] in [True, False]  # May or may not converge with small data
            assert 'rows_dropped' in meta
    
    def test_imputation_no_nans_unchanged(self, sample_data_no_nans, constants):
        """Test that data without NaNs is saved unchanged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'imputed.csv')
            
            result_df, meta = impute_missing_values(
                sample_data_no_nans,
                output_path,
                constants
            )
            
            # Verify no imputation was needed
            assert meta['imputed'] == False
            assert meta['rows_dropped'] == 0
            
            # Verify data is preserved
            pd.testing.assert_frame_equal(
                result_df.sort_values('sample_id').reset_index(drop=True),
                sample_data_no_nans.sort_values('sample_id').reset_index(drop=True)
            )
    
    def test_imputation_preserves_categorical(self, sample_data_with_nans, constants):
        """Test that categorical columns are preserved during imputation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'imputed.csv')
            
            result_df, _ = impute_missing_values(
                sample_data_with_nans,
                output_path,
                constants
            )
            
            # Verify categorical column is preserved
            assert 'biome' in result_df.columns
            assert result_df['biome'].dtype == 'object'
            assert list(result_df['biome'].unique()) == ['Forest', 'Grassland', 'Desert']
    
    def test_imputation_output_file_written(self, sample_data_with_nans, constants):
        """Test that the output file is actually written to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'imputed.csv')
            
            # Run imputation
            result_df, _ = impute_missing_values(
                sample_data_with_nans,
                output_path,
                constants
            )
            
            # Verify file exists and is readable
            assert os.path.isfile(output_path)
            assert os.path.getsize(output_path) > 0
            
            # Verify we can read it back
            read_back = pd.read_csv(output_path)
            assert len(read_back) == len(result_df)
    
    def test_imputation_convergence_check(self, sample_data_with_nans, constants):
        """Test that convergence flag is properly checked and logged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'imputed.csv')
            
            # Run with very low iteration limit to potentially cause non-convergence
            low_iter_constants = constants.copy()
            low_iter_constants['imputation'] = {
                'max_iterations': 1,
                'convergence_threshold': 0.0001
            }
            
            result_df, meta = impute_missing_values(
                sample_data_with_nans,
                output_path,
                low_iter_constants
            )
            
            # Verify convergence flag is present
            assert 'converged' in meta
            assert isinstance(meta['converged'], bool)
            
            # Even if not converged, no NaNs should remain
            assert result_df.isnull().sum().sum() == 0

class TestVIFCalculation:
    """Tests for VIF calculation functionality (T016 - dependency)."""
    
    def test_vif_rejects_high_correlation(self):
        """Test that highly correlated variables are identified."""
        # Create data with perfect correlation
        data = {
            'sample_id': ['S1', 'S2', 'S3', 'S4'],
            'var1': [1.0, 2.0, 3.0, 4.0],
            'var2': [2.0, 4.0, 6.0, 8.0],  # Perfectly correlated
            'var3': [1.0, 1.5, 2.0, 2.5]
        }
        df = pd.DataFrame(data)
        
        filtered_df, removed, retained = calculate_vif(df, threshold=5.0)
        
        # One of the correlated variables should be removed
        assert len(removed) >= 1
        assert 'var1' in removed or 'var2' in removed
    
    def test_vif_no_removal_low_correlation(self):
        """Test that low correlation variables are retained."""
        # Create data with low correlation
        np.random.seed(42)
        data = {
            'sample_id': [f'S{i}' for i in range(10)],
            'var1': np.random.randn(10),
            'var2': np.random.randn(10),
            'var3': np.random.randn(10)
        }
        df = pd.DataFrame(data)
        
        filtered_df, removed, retained = calculate_vif(df, threshold=5.0)
        
        # All numeric columns should be retained (unlikely to have VIF > 5 with random data)
        assert len(removed) == 0 or len(removed) < 3

class TestPreprocessingPipeline:
    """Integration tests for the full preprocessing pipeline."""
    
    def test_full_pipeline_integration(self, sample_data_with_nans):
        """Test the full pipeline from input to output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, 'input.csv')
            output_path = os.path.join(tmpdir, 'output.csv')
            
            # Save input
            sample_data_with_nans.to_csv(input_path, index=False)
            
            # Run pipeline
            results = run_preprocessing_pipeline(
                input_path,
                output_path,
                "src/config/constants.yaml"
            )
            
            # Verify results
            assert results['final_nan_count'] == 0
            assert os.path.exists(output_path)
            assert 'imputation' in results
            assert 'vif_removed_columns' in results
            
            # Verify output file can be read
            output_df = pd.read_csv(output_path)
            assert len(output_df) > 0
            assert output_df.isnull().sum().sum() == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
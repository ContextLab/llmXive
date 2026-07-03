"""
Unit tests for optimization_utils.py to ensure vectorization correctness and performance.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from optimization_utils import (
    vectorize_miller_indices_calculation,
    vectorize_sigma_calculation,
    vectorize_rodrigues_encoding,
    vectorize_feature_scaling,
    vectorize_missing_value_imputation,
    vectorize_diffusivity_calculation,
    vectorize_correlation_matrix,
    vectorize_outlier_detection
)

class TestVectorizeMillerIndices:
    def test_empty_array(self):
        """Test with empty input."""
        result = vectorize_miller_indices_calculation(np.array([]), np.eye(3))
        assert len(result) == 0
    
    def test_single_vector(self):
        """Test with a single boundary vector."""
        boundary_vec = np.array([[1, 0, 0]])
        lattice = np.eye(3)
        result = vectorize_miller_indices_calculation(boundary_vec, lattice)
        assert result.shape == (1, 3)
        assert np.all(result[0] == [1, 0, 0])
    
    def test_multiple_vectors(self):
        """Test with multiple boundary vectors."""
        boundary_vecs = np.array([
            [1, 0, 0],
            [0, 1, 0],
            [1, 1, 0]
        ])
        lattice = np.eye(3)
        result = vectorize_miller_indices_calculation(boundary_vecs, lattice)
        assert result.shape == (3, 3)
        # Check that results are integers
        assert np.all(result == result.astype(int))

class TestVectorizeSigmaCalculation:
    def test_empty_array(self):
        """Test with empty input."""
        result = vectorize_sigma_calculation(np.array([]))
        assert len(result) == 0
    
    def test_zero_angle(self):
        """Test with zero misorientation angle."""
        angles = np.array([0.0])
        result = vectorize_sigma_calculation(angles)
        # Should be minimum value of 1
        assert result[0] >= 1
    
    def test_small_angle(self):
        """Test with small misorientation angle."""
        angles = np.array([0.1])  # ~5.7 degrees
        result = vectorize_sigma_calculation(angles)
        assert result[0] >= 1
        assert isinstance(result[0], (int, np.integer))
    
    def test_multiple_angles(self):
        """Test with multiple angles."""
        angles = np.array([0.1, 0.2, 0.3])
        result = vectorize_sigma_calculation(angles)
        assert result.shape == (3,)
        assert np.all(result >= 1)

class TestVectorizeRodriguesEncoding:
    def test_empty_array(self):
        """Test with empty input."""
        result = vectorize_rodrigues_encoding(np.array([]).reshape(0, 3, 3))
        assert len(result) == 0
    
    def test_identity_rotation(self):
        """Test with identity rotation matrix."""
        identity = np.eye(3)
        rotations = np.array([identity])
        result = vectorize_rodrigues_encoding(rotations)
        # Rodrigues vector for identity should be zero
        assert np.allclose(result[0], [0, 0, 0], atol=1e-6)
    
    def test_90_degree_rotation(self):
        """Test with 90-degree rotation around z-axis."""
        theta = np.pi / 2
        rotation = np.array([
            [0, -1, 0],
            [1, 0, 0],
            [0, 0, 1]
        ])
        rotations = np.array([rotation])
        result = vectorize_rodrigues_encoding(rotations)
        assert result.shape == (1, 3)

class TestVectorizeFeatureScaling:
    def test_standard_scaling(self):
        """Test standard scaling."""
        data = pd.DataFrame({
            'a': [1, 2, 3, 4, 5],
            'b': [10, 20, 30, 40, 50]
        })
        scaled, params = vectorize_feature_scaling(data, ['a', 'b'], 'standard')
        
        # Check that mean is approximately 0 and std is approximately 1
        assert np.abs(scaled['a'].mean()) < 1e-10
        assert np.abs(scaled['a'].std() - 1.0) < 1e-10
        
    def test_minmax_scaling(self):
        """Test min-max scaling."""
        data = pd.DataFrame({
            'a': [1, 2, 3, 4, 5]
        })
        scaled, params = vectorize_feature_scaling(data, ['a'], 'minmax')
        
        # Check that min is 0 and max is 1
        assert scaled['a'].min() == 0.0
        assert scaled['a'].max() == 1.0

class TestVectorizeMissingValueImputation:
    def test_mean_imputation(self):
        """Test mean imputation."""
        data = pd.DataFrame({
            'a': [1, 2, np.nan, 4, 5],
            'b': [10, np.nan, 30, 40, 50]
        })
        imputed, params = vectorize_missing_value_imputation(data, 'mean')
        
        # Check that no NaN values remain
        assert imputed.isna().sum().sum() == 0
        # Check that imputed values are the mean
        assert imputed.loc[2, 'a'] == 3.0  # Mean of [1, 2, 4, 5]
        assert imputed.loc[1, 'b'] == 32.5  # Mean of [10, 30, 40, 50]
    
    def test_no_missing_values(self):
        """Test with no missing values."""
        data = pd.DataFrame({
            'a': [1, 2, 3, 4, 5]
        })
        imputed, params = vectorize_missing_value_imputation(data, 'mean')
        assert imputed.equals(data)

class TestVectorizeDiffusivityCalculation:
    def test_empty_arrays(self):
        """Test with empty arrays."""
        result = vectorize_diffusivity_calculation(
            np.array([]), np.array([]), np.array([])
        )
        assert len(result) == 0
    
    def test_single_value(self):
        """Test with single values."""
        T = np.array([300.0])
        Q = np.array([50000.0])  # J/mol
        D0 = np.array([1e-6])  # m²/s
        
        result = vectorize_diffusivity_calculation(T, Q, D0)
        assert result.shape == (1,)
        assert result[0] > 0
    
    def test_multiple_values(self):
        """Test with multiple values."""
        T = np.array([300.0, 400.0, 500.0])
        Q = np.array([50000.0, 50000.0, 50000.0])
        D0 = np.array([1e-6, 1e-6, 1e-6])
        
        result = vectorize_diffusivity_calculation(T, Q, D0)
        assert result.shape == (3,)
        assert np.all(result > 0)
        # Higher temperature should give higher diffusivity
        assert result[2] > result[1] > result[0]

class TestVectorizeCorrelationMatrix:
    def test_pearson_correlation(self):
        """Test Pearson correlation."""
        data = pd.DataFrame({
            'a': [1, 2, 3, 4, 5],
            'b': [2, 4, 6, 8, 10],
            'c': [5, 3, 1, 3, 5]
        })
        
        corr_matrix = vectorize_correlation_matrix(data, 'pearson')
        
        assert corr_matrix.shape == (3, 3)
        assert np.abs(corr_matrix.loc['a', 'b'] - 1.0) < 1e-10
        assert np.abs(corr_matrix.loc['a', 'a'] - 1.0) < 1e-10

class TestVectorizeOutlierDetection:
    def test_iqr_outlier_detection(self):
        """Test IQR-based outlier detection."""
        data = pd.DataFrame({
            'a': [1, 2, 3, 4, 5, 100],  # 100 is an outlier
            'b': [10, 20, 30, 40, 50, 60]
        })
        
        outliers = vectorize_outlier_detection(data, 'iqr', k=1.5)
        
        assert len(outliers) == 6
        assert outliers.iloc[5] == True  # Last row should be an outlier
        assert outliers.iloc[:5].sum() == 0  # First 5 rows should not be outliers
    
    def test_no_outliers(self):
        """Test with no outliers."""
        data = pd.DataFrame({
            'a': [1, 2, 3, 4, 5],
            'b': [10, 20, 30, 40, 50]
        })
        
        outliers = vectorize_outlier_detection(data, 'iqr', k=1.5)
        assert outliers.sum() == 0
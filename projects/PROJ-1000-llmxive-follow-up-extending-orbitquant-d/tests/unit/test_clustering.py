import pytest
import numpy as np
import json
import os
import sys
from pathlib import Path
from sklearn.cluster import KMeans
from scipy.linalg import qr

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.clustering import (
    compute_activation_histograms,
    compute_rotation_matrix_from_activations,
    cluster_variances_and_derive_matrices,
    run_clustering_pipeline
)

class TestActivationHistograms:
    def test_histogram_computation(self):
        """Test that histograms are computed correctly"""
        variances = {
            'layer_1': np.array([1.0, 2.0, 3.0, 4.0, 5.0]),
            'layer_2': np.array([10.0, 20.0, 30.0])
        }
        
        histograms = compute_activation_histograms(variances, n_bins=3)
        
        assert 'layer_1' in histograms
        assert 'layer_2' in histograms
        assert len(histograms['layer_1']['bin_edges']) == 4  # 3 bins -> 4 edges
        assert histograms['layer_1']['min'] == 1.0
        assert histograms['layer_1']['max'] == 5.0

    def test_empty_variances(self):
        """Test handling of empty variance arrays"""
        variances = {
            'layer_1': np.array([])
        }
        
        histograms = compute_activation_histograms(variances)
        
        assert 'layer_1' not in histograms or len(histograms.get('layer_1', {})) == 0

class TestRotationMatrix:
    def test_rotation_matrix_square(self):
        """Test that rotation matrix is square"""
        activations = np.random.randn(100, 64)
        matrix = compute_rotation_matrix_from_activations(activations, 64)
        
        assert matrix.shape[0] == matrix.shape[1] == 64

    def test_rotation_matrix_orthogonal(self):
        """Test that rotation matrix is approximately orthogonal"""
        activations = np.random.randn(100, 64)
        matrix = compute_rotation_matrix_from_activations(activations, 64)
        
        # Check orthogonality: Q @ Q.T ≈ I
        product = np.dot(matrix, matrix.T)
        identity = np.eye(64)
        error = np.linalg.norm(product - identity)
        
        assert error < 1e-5, f"Matrix not orthogonal: error={error}"

    def test_rotation_matrix_determinant(self):
        """Test that rotation matrix has positive determinant"""
        activations = np.random.randn(100, 64)
        matrix = compute_rotation_matrix_from_activations(activations, 64)
        
        det = np.linalg.det(matrix)
        assert det > 0, f"Determinant should be positive, got {det}"

    def test_1d_activations(self):
        """Test handling of 1D activation arrays"""
        activations = np.random.randn(100)
        matrix = compute_rotation_matrix_from_activations(activations, 64)
        
        assert matrix.shape == (64, 64)

class TestClustering:
    def test_clustering_with_sufficient_data(self):
        """Test clustering with enough samples"""
        variances = {
            'layer_1': np.random.randn(200) * 10 + 5  # 200 samples
        }
        
        report = cluster_variances_and_derive_matrices(variances, k=16)
        
        assert 'layers' in report
        assert 'subsets' in report
        assert 'boundaries' in report
        assert 'matrices' in report
        assert len(report['layers']) == 1
        assert len(report['matrices']) == 16

    def test_clustering_insufficient_data(self):
        """Test clustering with insufficient samples"""
        variances = {
            'layer_1': np.random.randn(10)  # Only 10 samples, less than K=16
        }
        
        report = cluster_variances_and_derive_matrices(variances, k=16)
        
        # Should handle gracefully, possibly skipping or using fallback
        assert 'layers' in report
        # May have empty layers or use fallback logic

    def test_matrix_shapes_in_report(self):
        """Test that all matrices in report have correct shape"""
        variances = {
            'layer_1': np.random.randn(200) * 10 + 5
        }
        
        report = cluster_variances_and_derive_matrices(variances, k=16)
        
        for i, matrix in enumerate(report['matrices']):
            matrix_np = np.array(matrix)
            assert matrix_np.shape[0] == matrix_np.shape[1], \
                f"Matrix {i} is not square: {matrix_np.shape}"

class TestPipeline:
    @pytest.fixture
    def sample_correlation_data(self, tmp_path):
        """Create sample correlation data for testing"""
        data = {
            'layer_1': list(np.random.randn(200) * 10 + 5),
            'layer_2': list(np.random.randn(200) * 5 + 2)
        }
        
        data_path = tmp_path / "correlation_results.json"
        with open(data_path, 'w') as f:
            json.dump(data, f)
        
        return str(data_path)

    def test_pipeline_end_to_end(self, sample_correlation_data, tmp_path):
        """Test the complete clustering pipeline"""
        output_path = tmp_path / "clustering_report.json"
        
        report = run_clustering_pipeline(
            data_path=sample_correlation_data,
            output_path=str(output_path)
        )
        
        # Verify output file exists
        assert output_path.exists()
        
        # Verify report structure
        assert 'layers' in report
        assert 'matrices' in report
        assert len(report['matrices']) == 16  # K=16

    def test_pipeline_file_not_found(self, tmp_path):
        """Test pipeline with missing input file"""
        output_path = tmp_path / "clustering_report.json"
        
        with pytest.raises(FileNotFoundError):
            run_clustering_pipeline(
                data_path="nonexistent.json",
                output_path=str(output_path)
            )

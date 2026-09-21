import os
import json
import tempfile
import numpy as np
import pytest
import torch

from analysis.clustering import (
    compute_activation_histograms,
    compute_rotation_matrix_from_activations,
    run_clustering_pipeline
)

class TestActivationHistograms:
    def test_histogram_computation(self):
        """Test that histograms are computed correctly."""
        # Create a simple tensor
        activations = torch.tensor([
            [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
            [[7.0, 8.0, 9.0], [10.0, 11.0, 12.0]]
        ])
        
        histograms = compute_activation_histograms(activations, num_bins=3)
        
        assert histograms.shape == (2, 3), f"Expected shape (2, 3), got {histograms.shape}"
        assert np.allclose(histograms.sum(axis=1), 1.0, atol=1e-6), "Histograms should sum to 1"
    
    def test_histogram_normalization(self):
        """Test that histograms are properly normalized."""
        activations = torch.ones(1, 1, 10, 10)  # All ones
        histograms = compute_activation_histograms(activations, num_bins=5)
        
        # With all ones, the histogram should be concentrated in one bin
        assert histograms.shape == (1, 5)
        assert np.max(histograms) > 0.5, "One bin should have significant weight"

class TestRotationMatrixComputation:
    def test_rotation_matrix_shape(self):
        """Test that rotation matrices have correct shape."""
        # Create dummy activation data
        num_samples = 50
        num_bins = 20
        activations = np.random.randn(num_samples, num_bins)
        
        k = 4
        rotation_matrix = compute_rotation_matrix_from_activations(activations, k=k)
        
        assert rotation_matrix.shape == (k, num_bins), f"Expected shape ({k}, {num_bins})"
    
    def test_rotation_matrix_normalization(self):
        """Test that rotation vectors are normalized."""
        num_samples = 50
        num_bins = 20
        activations = np.random.randn(num_samples, num_bins)
        
        k = 4
        rotation_matrix = compute_rotation_matrix_from_activations(activations, k=k)
        
        # Check that each row has unit norm (approximately)
        norms = np.linalg.norm(rotation_matrix, axis=1)
        assert np.allclose(norms, 1.0, atol=1e-5), "Rotation vectors should be normalized"

class TestClusteringPipeline:
    def test_full_pipeline(self):
        """Test the full clustering pipeline."""
        # Create temporary directory and files
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "activations.csv")
            output_path = os.path.join(tmpdir, "clustering_report.json")
            
            # Create dummy activation data
            with open(input_path, 'w') as f:
                f.write("layer_name,subset_id,histogram\n")
                for i in range(20):
                    hist = ','.join(map(str, np.random.rand(10)))
                    f.write(f"layer_{i%3},{i},{hist}\n")
            
            # Run pipeline
            report = run_clustering_pipeline(
                activation_data_path=input_path,
                output_path=output_path,
                k=4,
                num_bins=10
            )
            
            # Verify output file exists
            assert os.path.exists(output_path), "Output file should be created"
            
            # Verify report structure
            assert 'layers' in report
            assert 'subsets' in report
            assert 'boundaries' in report
            assert 'rotation_matrices' in report
            assert 'k' in report
            
            assert report['k'] == 4
            assert len(report['rotation_matrices']) == 4
    
    def test_pipeline_with_existing_output(self):
        """Test that pipeline can read and validate existing output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "activations.csv")
            output_path = os.path.join(tmpdir, "clustering_report.json")
            
            # Create dummy activation data
            with open(input_path, 'w') as f:
                f.write("layer_name,subset_id,histogram\n")
                for i in range(20):
                    hist = ','.join(map(str, np.random.rand(10)))
                    f.write(f"layer_{i%3},{i},{hist}\n")
            
            # Run pipeline
            run_clustering_pipeline(
                activation_data_path=input_path,
                output_path=output_path,
                k=4,
                num_bins=10
            )
            
            # Load and verify
            with open(output_path, 'r') as f:
                report = json.load(f)
            
            assert 'rotation_matrices' in report
            assert len(report['rotation_matrices']) == 4
    
    def test_pipeline_k_adjustment(self):
        """Test that K is adjusted when samples < K."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "activations.csv")
            output_path = os.path.join(tmpdir, "clustering_report.json")
            
            # Create very small dataset
            with open(input_path, 'w') as f:
                f.write("layer_name,subset_id,histogram\n")
                for i in range(3):  # Only 3 samples
                    hist = ','.join(map(str, np.random.rand(10)))
                    f.write(f"layer_0,{i},{hist}\n")
            
            # Run pipeline with K=10 (more than samples)
            report = run_clustering_pipeline(
                activation_data_path=input_path,
                output_path=output_path,
                k=10,
                num_bins=10
            )
            
            # K should be adjusted down
            assert report['k'] < 10
            assert len(report['rotation_matrices']) == report['k']

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

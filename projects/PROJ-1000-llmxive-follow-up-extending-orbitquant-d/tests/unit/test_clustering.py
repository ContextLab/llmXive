import os
import json
import tempfile
import numpy as np
import pytest
from pathlib import Path

# Mock the clustering functions for unit testing
# We test the logic of matrix derivation and report generation
# without needing the full pipeline.

def test_compute_rotation_matrix():
    """Test that rotation matrices are orthogonal and of correct shape."""
    from code.analysis.clustering import compute_rotation_matrix_from_activations
    
    # Create dummy activation data: 100 samples, 10 features
    np.random.seed(42)
    activations = np.random.randn(100, 10)
    
    k = 4
    matrices = compute_rotation_matrix_from_activations(activations, k=k)
    
    assert len(matrices) == k
    for i, R in enumerate(matrices):
        assert R.shape == (10, 10), f"Matrix {i} has wrong shape: {R.shape}"
        # Check orthogonality: R * R.T should be close to identity
        product = np.dot(R, R.T)
        identity = np.eye(10)
        assert np.allclose(product, identity, atol=1e-5), f"Matrix {i} is not orthogonal"

def test_run_clustering_pipeline():
    """Test the full pipeline with dummy data."""
    from code.analysis.clustering import run_clustering_pipeline
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy input CSV
        input_file = Path(tmpdir) / "activation_variances_train.csv"
        with open(input_file, 'w') as f:
            f.write("prompt_id,layer_0,layer_1,layer_2\n")
            for i in range(50):
                f.write(f"p{i},{np.random.rand()},{np.random.rand()},{np.random.rand()}\n")
        
        output_file = Path(tmpdir) / "clustering_report.json"
        
        # Run pipeline
        report = run_clustering_pipeline(str(input_file), str(output_file), k=2)
        
        # Verify output file exists
        assert os.path.exists(output_file)
        
        # Verify report structure
        assert "k" in report
        assert "n_layers" in report
        assert "layers" in report
        assert "subsets" in report
        assert len(report["subsets"]) == 2
        
        for subset in report["subsets"]:
            assert "cluster_id" in subset
            assert "size" in subset
            assert "boundaries" in subset
            assert "rotation_matrix" in subset
            # Check that rotation matrix is a list of lists
            assert isinstance(subset["rotation_matrix"], list)
            assert len(subset["rotation_matrix"]) == report["n_layers"]

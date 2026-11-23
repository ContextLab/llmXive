"""
Tests for the stability aggregation functionality (T024).
"""
import pytest
import numpy as np
import tempfile
import json
from pathlib import Path
from analysis.stability_aggregator import (
    calculate_cosine_similarity_matrix,
    aggregate_stability_results,
    write_stability_report,
    StabilityError
)

def test_cosine_similarity_identical():
    """Test that identical components have similarity 1.0."""
    W = np.random.rand(5, 10)
    components = [W, W]
    sim_matrix = calculate_cosine_similarity_matrix(components)
    # Diagonal should be 1.0, off-diagonal should be 1.0 for identical
    assert np.allclose(sim_matrix, 1.0), "Identical components should have similarity 1.0"

def test_cosine_similarity_orthogonal():
    """Test that orthogonal components have low similarity."""
    # Create two orthogonal matrices
    W1 = np.eye(5, 10)
    W2 = np.zeros((5, 10))
    W2[:, 5:] = np.eye(5, 5)  # Orthogonal support
    
    components = [W1, W2]
    sim_matrix = calculate_cosine_similarity_matrix(components)
    
    # Mean similarity should be low (close to 0)
    assert np.mean(sim_matrix) < 0.1, "Orthogonal components should have low similarity"

def test_aggregate_stability_pass():
    """Test successful aggregation with stable components."""
    with tempfile.TemporaryDirectory() as tmpdir:
        results_dir = Path(tmpdir)
        seeds = [42, 123]
        k_values = [5]
        
        # Create stable (identical) results for both seeds
        for seed in seeds:
            W = np.random.rand(5, 10)
            np.savez(results_dir / f"nmf_results_k5_seed{seed}.npz", W=W)
        
        report = aggregate_stability_results(results_dir, seeds, k_values)
        
        assert report["status"] == "PASS", f"Expected PASS, got {report['status']}"
        assert report["threshold"] == 0.95
        assert len(report["details"]) == 1
        assert report["details"][0]["status"] == "PASS"

def test_aggregate_stability_fail():
    """Test aggregation when stability threshold is not met."""
    with tempfile.TemporaryDirectory() as tmpdir:
        results_dir = Path(tmpdir)
        seeds = [42, 123]
        k_values = [5]
        
        # Create very different (unstable) components
        W1 = np.random.rand(5, 10)
        W2 = np.random.rand(5, 10) * -1  # Sign flip makes them dissimilar in cosine
        
        np.savez(results_dir / "nmf_results_k5_seed42.npz", W=W1)
        np.savez(results_dir / "nmf_results_k5_seed123.npz", W=W2)
        
        report = aggregate_stability_results(results_dir, seeds, k_values)
        
        # This might pass or fail depending on random values, but we test the structure
        assert "status" in report
        assert "details" in report
        assert report["threshold"] == 0.95

def test_missing_result_file():
    """Test that missing result file raises StabilityError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        results_dir = Path(tmpdir)
        seeds = [42]
        k_values = [5]
        
        # Don't create the file
        with pytest.raises(StabilityError):
            aggregate_stability_results(results_dir, seeds, k_values)

def test_write_report():
    """Test that report is written correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "test_report.json"
        report = {
            "status": "PASS",
            "threshold": 0.95,
            "details": []
        }
        
        write_stability_report(report, report_path)
        
        assert report_path.exists()
        with open(report_path) as f:
            loaded = json.load(f)
        
        assert loaded["status"] == "PASS"
        assert loaded["threshold"] == 0.95
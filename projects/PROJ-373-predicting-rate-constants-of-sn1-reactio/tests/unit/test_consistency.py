import pytest
import numpy as np
from analysis.consistency import compute_kendall_tau_consistency, generate_consistency_report
import tempfile
import os
from pathlib import Path

def test_compute_kendall_tau_consistency_identical():
    """Test that identical rankings yield tau = 1.0"""
    rankings = [
        ["A", "B", "C"],
        ["A", "B", "C"],
        ["A", "B", "C"]
    ]
    metrics = compute_kendall_tau_consistency(rankings)
    assert metrics["mean_tau"] == 1.0
    assert metrics["min_tau"] == 1.0
    assert metrics["max_tau"] == 1.0

def test_compute_kendall_tau_consistency_opposite():
    """Test that opposite rankings yield low tau"""
    rankings = [
        ["A", "B", "C"],
        ["C", "B", "A"]
    ]
    metrics = compute_kendall_tau_consistency(rankings)
    # For 3 items, max inversion is 3, total pairs is 3. Tau = (3-3)/(3) = 0? 
    # Actually for 3 items, max discordant is 3. 
    # A,B,C vs C,B,A:
    # (A,C): A<C in 1, A>C in 2 -> discordant
    # (A,B): A<B in 1, A>B in 2 -> discordant
    # (B,C): B<C in 1, B>C in 2 -> discordant
    # All 3 pairs discordant. Tau = (0 - 3) / 3 = -1.0
    assert metrics["min_tau"] == -1.0

def test_generate_consistency_report():
    """Test report generation"""
    seed_results = {
        42: {"metrics": {"r2": 0.8}, "rankings": ["A", "B", "C"]},
        123: {"metrics": {"r2": 0.75}, "rankings": ["A", "C", "B"]}
    }
    consistency_metrics = {"mean_tau": 0.5, "min_tau": 0.4, "max_tau": 0.6}
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_report.md"
        generate_consistency_report(seed_results, consistency_metrics, output_path)
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "SHAP Consistency Report" in content
        assert "42" in content
        assert "123" in content
        assert "0.8" in content
        assert "0.5" in content
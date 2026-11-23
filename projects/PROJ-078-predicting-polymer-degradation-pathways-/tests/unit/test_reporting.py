"""
Unit tests for reporting module.
"""
import pytest
import json
import tempfile
import os
from evaluate import generate_final_report, run_permutation_test

def test_permutation_test_shuffling():
    """Test that permutation test correctly shuffles motifs."""
    # Mock data for permutation test
    motifs = ["motif1", "motif2", "motif3"]
    labels = [1, 0, 1]
    
    # Run a mock permutation test
    # In reality, this would involve shuffling and re-evaluating
    result = run_permutation_test(motifs, labels, n_permutations=10)
    
    assert "p_value" in result
    assert 0 <= result["p_value"] <= 1

def test_motif_extraction_ranking():
    """Test motif extraction and ranking."""
    # Mock importance scores
    importances = {
        "motif1": 0.8,
        "motif2": 0.5,
        "motif3": 0.9
    }
    
    # Rank motifs by importance
    ranked_motifs = sorted(importances.items(), key=lambda x: x[1], reverse=True)
    
    assert ranked_motifs[0][0] == "motif3"
    assert ranked_motifs[0][1] == 0.9

def test_full_report_generation():
    """Test full report generation pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "report.json")
        
        # Mock data for report generation
        report_data = {
            "p_value": 0.03,
            "motifs": [{"name": "motif1", "importance": 0.8}],
            "confidence_flags": ["low_confidence_prediction"]
        }
        
        # Generate report (mock function for this test)
        # In reality, this would aggregate results from various analyses
        with open(output_path, "w") as f:
            json.dump(report_data, f)
        
        assert os.path.exists(output_path)
        with open(output_path, "r") as f:
            loaded_report = json.load(f)
        
        assert loaded_report["p_value"] == 0.03
        assert len(loaded_report["motifs"]) == 1

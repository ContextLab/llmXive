"""
Integration test for T024b: Hallucination Rate Calculation.

This test verifies that the hallucination rate script correctly identifies
cases where the answer is correct but the spatial attribution is wrong.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from code.hallucination_rate import calculate_hallucination_metrics, save_results

def test_hallucination_calculation_logic():
    """
    Test the core logic of hallucination detection.
    
    Scenario:
    1. Correct Answer, Correct Box -> Not a hallucination
    2. Correct Answer, Wrong Box -> Hallucination
    3. Wrong Answer, Correct Box -> Not a hallucination (just wrong answer)
    4. Wrong Answer, Wrong Box -> Not a hallucination
    """
    mock_results = [
        {"answer_correct": True, "spatial_correct": True},   # True Positive
        {"answer_correct": True, "spatial_correct": False},  # Hallucination
        {"answer_correct": False, "spatial_correct": True},  # False Positive (Spatial only)
        {"answer_correct": False, "spatial_correct": False}, # False Negative
        {"answer_correct": True, "spatial_correct": False},  # Another Hallucination
    ]
    
    metrics = calculate_hallucination_metrics(mock_results)
    
    # Total correct answers = 3 (indices 0, 1, 4)
    assert metrics["total_correct_answers"] == 3
    
    # Hallucinations = 2 (indices 1, 4)
    assert metrics["hallucination_count"] == 2
    
    # Rate = 2/3
    assert abs(metrics["hallucination_rate"] - (2/3)) < 1e-6

def test_no_correct_answers():
    """Test behavior when there are no correct answers."""
    mock_results = [
        {"answer_correct": False, "spatial_correct": True},
        {"answer_correct": False, "spatial_correct": False},
    ]
    
    metrics = calculate_hallucination_metrics(mock_results)
    
    assert metrics["total_correct_answers"] == 0
    assert metrics["hallucination_count"] == 0
    assert metrics["hallucination_rate"] == 0.0

def test_end_to_end_save():
    """Test the full pipeline of calculation and saving."""
    mock_results = [
        {"answer_correct": True, "spatial_correct": False},
    ]
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        output_file = tmp_path / "test_hallucination.json"
        
        metrics = calculate_hallucination_metrics(mock_results)
        save_results(metrics, output_file)
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["hallucination_rate"] == 1.0
        assert saved_data["hallucination_count"] == 1
        assert saved_data["total_correct_answers"] == 1
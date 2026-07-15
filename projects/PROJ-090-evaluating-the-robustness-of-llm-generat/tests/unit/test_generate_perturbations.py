"""
Unit tests for the perturbation generation pipeline (T018).
Verifies the logic of generating, scoring, and filtering variants.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.generate_perturbations import (
    generate_and_filter_perturbations,
    load_humaneval_tasks,
    save_results,
    SEMANTIC_THRESHOLD
)

def test_generate_and_filter_logic():
    """
    Test that the pipeline correctly filters based on semantic score.
    We mock the external dependencies (generation and validation) to
    control the scores and verify the filtering logic.
    """
    # Mock task
    mock_task = {
        "task_id": "test_001",
        "prompt": "def add(a, b): return a + b",
        "canonical_solution": "return a + b"
    }
    
    # Mock candidates
    mock_candidates = [
        {"type": "synonym", "text": "def plus(a, b): return a + b"},
        {"type": "typo", "text": "def add(a, b): retunr a + b"},
        {"type": "rephrase", "text": "def add_numbers(a, b): return a + b"}
    ]

    # Mock validation results:
    # 1. Valid (score > threshold)
    # 2. Invalid (score < threshold)
    # 3. Valid (score > threshold)
    mock_validation_results = [
        {"type": "synonym", "perturbed": "def plus(a, b): return a + b", "score": 0.98, "valid": True},
        {"type": "typo", "perturbed": "def add(a, b): retunr a + b", "score": 0.85, "valid": False},
        {"type": "rephrase", "perturbed": "def add_numbers(a, b): return a + b", "score": 0.96, "valid": True}
    ]

    # Patch the external functions
    with patch('code.data.generate_perturbations.generate_perturbation_variants', return_value=mock_candidates), \
         patch('code.data.generate_perturbations.validate_perturbation_batch', return_value=mock_validation_results):
        
        result = generate_and_filter_perturbations([mock_task])
        
        # Assert we got exactly 2 valid perturbations (the ones with score > 0.95)
        assert len(result) == 2, f"Expected 2 valid perturbations, got {len(result)}"
        
        # Verify the types are correct
        types = [r["perturbation_type"] for r in result]
        assert "synonym" in types
        assert "rephrase" in types
        assert "typo" not in types

        # Verify scores are preserved
        for r in result:
            assert r["semantic_score"] > SEMANTIC_THRESHOLD

def test_empty_input():
    """Test that empty input list returns empty output."""
    result = generate_and_filter_perturbations([])
    assert result == []

def test_save_results_creates_file():
    """Test that save_results actually writes a JSONL file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_output.jsonl"
        test_data = [
            {"id": 1, "text": "hello"},
            {"id": 2, "text": "world"}
        ]
        
        save_results(test_data, str(output_path))
        
        assert output_path.exists(), "Output file was not created"
        
        with open(output_path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 2, f"Expected 2 lines, got {len(lines)}"
        
        # Verify JSON validity
        for line in lines:
            json.loads(line) # Should not raise

def test_filtering_threshold_boundary():
    """Test behavior exactly at the threshold boundary."""
    mock_task = {"task_id": "boundary_test", "prompt": "test"}
    mock_candidates = [{"type": "test", "text": "test_var"}]
    
    # Exactly at threshold (0.95) should be invalid because condition is > 0.95
    mock_results = [{"type": "test", "perturbed": "test_var", "score": 0.95, "valid": False}]
    
    with patch('code.data.generate_perturbations.generate_perturbation_variants', return_value=mock_candidates), \
         patch('code.data.generate_perturbations.validate_perturbation_batch', return_value=mock_results):
        
        result = generate_and_filter_perturbations([mock_task])
        assert len(result) == 0, "Score exactly at threshold should be filtered out"
    
    # Slightly above threshold
    mock_results_above = [{"type": "test", "perturbed": "test_var", "score": 0.95001, "valid": True}]
    
    with patch('code.data.generate_perturbations.generate_perturbation_variants', return_value=mock_candidates), \
         patch('code.data.generate_perturbations.validate_perturbation_batch', return_value=mock_results_above):
        
        result = generate_and_filter_perturbations([mock_task])
        assert len(result) == 1, "Score above threshold should be retained"

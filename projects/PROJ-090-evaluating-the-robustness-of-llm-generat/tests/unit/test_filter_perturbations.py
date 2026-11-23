"""
Unit tests for the filter_perturbations module (T018).

Tests verify:
1. Filtering logic correctly retains candidates with raw_score > 0.95.
2. Halt condition is triggered when zero candidates remain.
3. Output file is correctly formatted.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data.filter_perturbations import (
    filter_candidates,
    load_raw_candidates,
    save_filtered_results,
    save_halt_report,
    main,
    THRESHOLD
)

@pytest.fixture
def sample_candidates():
    """Fixture providing sample candidate data."""
    return [
        {"task_id": "task1", "perturbation_type": "synonym", "raw_score": 0.98, "is_valid": True, "candidate_text": "def foo(): pass"},
        {"task_id": "task1", "perturbation_type": "typo", "raw_score": 0.92, "is_valid": True, "candidate_text": "def fo(): pass"},
        {"task_id": "task2", "perturbation_type": "rephrase", "raw_score": 0.96, "is_valid": True, "candidate_text": "def bar(): pass"},
        {"task_id": "task2", "perturbation_type": "synonym", "raw_score": 0.94, "is_valid": True, "candidate_text": "def baz(): pass"},
        {"task_id": "task3", "perturbation_type": "typo", "raw_score": 0.99, "is_valid": True, "candidate_text": "def qux(): pass"},
    ]

@pytest.fixture
def empty_candidates():
    """Fixture providing empty candidate list."""
    return []

@pytest.fixture
def all_low_score_candidates():
    """Fixture providing candidates all below threshold."""
    return [
        {"task_id": "task1", "perturbation_type": "synonym", "raw_score": 0.85, "is_valid": True, "candidate_text": "def foo(): pass"},
        {"task_id": "task2", "perturbation_type": "typo", "raw_score": 0.90, "is_valid": True, "candidate_text": "def bar(): pass"},
    ]

@pytest.fixture
def temp_dir(tmp_path):
    """Fixture providing a temporary directory for file operations."""
    return tmp_path

def test_filter_candidates_retains_high_scores(sample_candidates):
    """Test that filter_candidates retains only candidates with raw_score > 0.95."""
    filtered = filter_candidates(sample_candidates, THRESHOLD)

    assert len(filtered) == 3  # 0.98, 0.96, 0.99
    assert all(c['raw_score'] > THRESHOLD for c in filtered)
    
    # Verify specific candidates are retained
    task_ids = [c['task_id'] for c in filtered]
    assert 'task1' in task_ids  # 0.98 score
    assert 'task2' in task_ids  # 0.96 score
    assert 'task3' in task_ids  # 0.99 score

    # Verify low score candidates are removed
    assert not any(c['raw_score'] <= THRESHOLD for c in filtered)

def test_filter_candidates_empty_input(empty_candidates):
    """Test that filter_candidates returns empty list for empty input."""
    filtered = filter_candidates(empty_candidates, THRESHOLD)
    assert filtered == []

def test_filter_candidates_all_low_scores(all_low_score_candidates):
    """Test that filter_candidates returns empty list when all scores are low."""
    filtered = filter_candidates(all_low_score_candidates, THRESHOLD)
    assert filtered == []

def test_filter_candidates_custom_threshold(sample_candidates):
    """Test filtering with a custom threshold."""
    custom_threshold = 0.90
    filtered = filter_candidates(sample_candidates, custom_threshold)
    
    assert len(filtered) == 4  # 0.98, 0.96, 0.94, 0.99
    assert all(c['raw_score'] > custom_threshold for c in filtered)

def test_save_filtered_results(temp_dir, sample_candidates):
    """Test that save_filtered_results correctly writes JSON."""
    output_path = temp_dir / "filtered.json"
    save_filtered_results(sample_candidates, output_path)
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        saved_data = json.load(f)
    
    assert len(saved_data) == len(sample_candidates)
    assert saved_data == sample_candidates

def test_save_halt_report(temp_dir):
    """Test that save_halt_report creates correct halt report."""
    halt_path = temp_dir / "halt.json"
    save_halt_report("ZERO_YIELD", halt_path)
    
    assert halt_path.exists()
    
    with open(halt_path, 'r') as f:
        report = json.load(f)
    
    assert report['reason'] == "ZERO_YIELD"
    assert 'details' in report
    assert 'timestamp' in report

def test_main_zero_yield(temp_dir, all_low_score_candidates):
    """Test that main() triggers halt when zero candidates remain."""
    input_path = temp_dir / "input.json"
    output_path = temp_dir / "output.json"
    halt_path = temp_dir / "halt.json"
    
    # Write input data
    with open(input_path, 'w') as f:
        json.dump(all_low_score_candidates, f)
    
    # Mock paths
    with patch('code.data.filter_perturbations.INPUT_PATH', input_path), \
         patch('code.data.filter_perturbations.OUTPUT_PATH', output_path), \
         patch('code.data.filter_perturbations.HALT_REPORT_PATH', halt_path):
        
        result = main()
        
        assert result == 1  # Exit code 1 for failure
        assert halt_path.exists()
        
        with open(halt_path, 'r') as f:
            report = json.load(f)
        
        assert report['reason'] == "ZERO_YIELD"
        assert not output_path.exists()

def test_main_success(temp_dir, sample_candidates):
    """Test that main() succeeds when candidates are retained."""
    input_path = temp_dir / "input.json"
    output_path = temp_dir / "output.json"
    halt_path = temp_dir / "halt.json"
    
    # Write input data
    with open(input_path, 'w') as f:
        json.dump(sample_candidates, f)
    
    # Mock paths
    with patch('code.data.filter_perturbations.INPUT_PATH', input_path), \
         patch('code.data.filter_perturbations.OUTPUT_PATH', output_path), \
         patch('code.data.filter_perturbations.HALT_REPORT_PATH', halt_path):
        
        result = main()
        
        assert result == 0  # Exit code 0 for success
        assert output_path.exists()
        assert not halt_path.exists()  # No halt report on success
        
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        assert len(saved_data) == 3  # Only high-score candidates

def test_main_missing_input_file(temp_dir):
    """Test that main() triggers halt when input file is missing."""
    input_path = temp_dir / "nonexistent.json"
    output_path = temp_dir / "output.json"
    halt_path = temp_dir / "halt.json"
    
    # Mock paths
    with patch('code.data.filter_perturbations.INPUT_PATH', input_path), \
         patch('code.data.filter_perturbations.OUTPUT_PATH', output_path), \
         patch('code.data.filter_perturbations.HALT_REPORT_PATH', halt_path):
        
        result = main()
        
        assert result == 1
        assert halt_path.exists()
        
        with open(halt_path, 'r') as f:
            report = json.load(f)
        
        assert report['reason'] == "INPUT_NOT_FOUND"
"""
Unit tests for the curation filter logic (T014a).
"""
import json
import tempfile
from pathlib import Path
import pytest

# Import the function to test
from data.curate import filter_hard_instances, load_derived_ground_truth

@pytest.fixture
def temp_dataset_file():
    """Create a temporary dataset file with initial_coverage scores."""
    data = [
        {"issue_id": "1", "initial_coverage": 0.1, "code": "x=1"},
        {"issue_id": "2", "initial_coverage": 0.2, "code": "x=2"},
        {"issue_id": "3", "initial_coverage": 0.3, "code": "x=3"},
        {"issue_id": "4", "initial_coverage": 0.4, "code": "x=4"},
        {"issue_id": "5", "initial_coverage": 0.5, "code": "x=5"},
        {"issue_id": "6", "initial_coverage": 0.6, "code": "x=6"},
        {"issue_id": "7", "initial_coverage": 0.7, "code": "x=7"},
        {"issue_id": "8", "initial_coverage": 0.8, "code": "x=8"},
        {"issue_id": "9", "initial_coverage": 0.9, "code": "x=9"},
        {"issue_id": "10", "initial_coverage": 1.0, "code": "x=10"},
    ]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for item in data:
            f.write(json.dumps(item) + '\n')
        return Path(f.name)

@pytest.fixture
def temp_gt_file():
    """Create a temporary ground truth file."""
    data = [
        {"issue_id": "1", "ground_truth_lines": [1, 2], "original_hash": "abc"},
        {"issue_id": "2", "ground_truth_lines": [2, 3], "original_hash": "def"},
        {"issue_id": "3", "ground_truth_lines": [3, 4], "original_hash": "ghi"},
        {"issue_id": "4", "ground_truth_lines": [4, 5], "original_hash": "jkl"},
        {"issue_id": "5", "ground_truth_lines": [5, 6], "original_hash": "mno"},
        {"issue_id": "6", "ground_truth_lines": [6, 7], "original_hash": "pqr"},
        {"issue_id": "7", "ground_truth_lines": [7, 8], "original_hash": "stu"},
        {"issue_id": "8", "ground_truth_lines": [8, 9], "original_hash": "vwx"},
        {"issue_id": "9", "ground_truth_lines": [9, 10], "original_hash": "yz1"},
        {"issue_id": "10", "ground_truth_lines": [10, 11], "original_hash": "234"},
    ]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for item in data:
            f.write(json.dumps(item) + '\n')
        return Path(f.name)

def test_filter_hard_instances_percentile(temp_dataset_file, temp_gt_file):
    """Test that the bottom 20% (2 items) are selected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "hard_subset.jsonl"
        
        gt_map = load_derived_ground_truth(temp_gt_file)
        
        result = filter_hard_instances(
            input_dataset_path=temp_dataset_file,
            output_path=output_path,
            ground_truth_map=gt_map,
            percentile=20
        )
        
        # Should select bottom 20% of 10 items = 2 items
        assert len(result) == 2
        
        # Should be the ones with lowest coverage: 0.1 and 0.2
        assert result[0]['issue_id'] == '1'
        assert result[0]['initial_coverage'] == 0.1
        assert result[1]['issue_id'] == '2'
        assert result[1]['initial_coverage'] == 0.2
        
        # Verify ground_truth_lines were enriched
        assert 'ground_truth_lines' in result[0]
        assert result[0]['ground_truth_lines'] == [1, 2]
        
        # Verify file was written
        assert output_path.exists()
        with open(output_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 2

def test_filter_hard_instances_missing_gt(temp_dataset_file, temp_gt_file):
    """Test handling of missing ground truth entries."""
    # Remove one GT entry
    gt_map = load_derived_ground_truth(temp_gt_file)
    del gt_map['1']
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "hard_subset.jsonl"
        
        # This should not crash, but log a warning and use empty list
        result = filter_hard_instances(
            input_dataset_path=temp_dataset_file,
            output_path=output_path,
            ground_truth_map=gt_map,
            percentile=20
        )
        
        assert len(result) == 2
        # The first one (issue 1) should have empty ground_truth_lines
        assert result[0]['issue_id'] == '1'
        assert result[0]['ground_truth_lines'] == []
        # The second one should have data
        assert result[1]['ground_truth_lines'] == [2, 3]

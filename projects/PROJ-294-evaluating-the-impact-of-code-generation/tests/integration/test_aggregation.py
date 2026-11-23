import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
from code.analyze_metrics import aggregate_metrics_to_json, apply_pairwise_exclusion, calculate_code_metrics

def test_aggregate_metrics_schema():
    """Verify that aggregate_metrics_to_json produces the correct schema."""
    # Mock input data
    mock_samples = [
        {
            "task_id": "HumanEval/0",
            "source_type": "human",
            "code": "def add(a, b):\n    return a + b",
            "test_code": "assert add(1, 2) == 3"
        },
        {
            "task_id": "HumanEval/0",
            "source_type": "llm",
            "code": "def add(a, b):\n    return a + b",
            "test_code": "assert add(1, 2) == 3"
        }
    ]
    
    # Run aggregation
    # We need to mock the external dependencies (pytest, radon) to avoid execution issues in unit tests
    with patch('code.analyze_metrics.execute_test_suite', return_value=True), \
         patch('code.analyze_metrics.execute_coverage_test', return_value=100.0), \
         patch('code.analyze_metrics.cc_visit', return_value=[MagicMock(complexity=1)]), \
         patch('code.analyze_metrics.radon_raw_analyze', return_value=MagicMock(vocabulary=MagicMock(volume=50.0))):
        
        output_path = "data/analysis/test_metrics.json"
        result = aggregate_metrics_to_json(mock_samples, output_path)
        
        # Verify file exists
        assert os.path.exists(output_path)
        
        # Verify content
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 2
        for record in data:
            assert "task_id" in record
            assert "source_type" in record
            assert "cyclomatic_complexity" in record
            assert "halstead_volume" in record
            assert "branch_coverage_pct" in record
            assert "pass_rate" in record
            
            # Verify types
            assert isinstance(record["task_id"], str)
            assert isinstance(record["source_type"], str)
            assert isinstance(record["cyclomatic_complexity"], (int, float))
            assert isinstance(record["halstead_volume"], (int, float))
            assert isinstance(record["branch_coverage_pct"], (int, float))
            assert isinstance(record["pass_rate"], (int, float))
        
        # Cleanup
        os.remove(output_path)

def test_pairwise_exclusion_null_coverage():
    """Test T042a and T042b logic: removal of null coverage and incomplete pairs."""
    records = [
        {"task_id": "1", "source_type": "human", "branch_coverage_pct": 80.0},
        {"task_id": "1", "source_type": "llm", "branch_coverage_pct": 75.0},
        {"task_id": "2", "source_type": "human", "branch_coverage_pct": None}, # T042a: remove
        {"task_id": "2", "source_type": "llm", "branch_coverage_pct": 90.0},
        {"task_id": "3", "source_type": "human", "branch_coverage_pct": 85.0},
        {"task_id": "4", "source_type": "human", "branch_coverage_pct": 85.0} # Incomplete pair
    ]
    
    result = apply_pairwise_exclusion(records)
    
    # Task 2 should be removed entirely because one side had null coverage
    # Task 4 should be removed because it has no pair
    # Task 1 should remain
    assert len(result) == 2
    task_ids = [r["task_id"] for r in result]
    assert "1" in task_ids
    assert "2" not in task_ids
    assert "4" not in task_ids
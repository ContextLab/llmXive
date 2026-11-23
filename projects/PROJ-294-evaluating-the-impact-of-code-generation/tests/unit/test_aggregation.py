import json
import os
import tempfile
import pytest
from code.analyze_metrics import aggregate_metrics_to_json, apply_pairwise_exclusion_gate

def test_aggregation_schema():
    """Test that aggregated metrics have the correct schema."""
    input_data = [
        {
            "task_id": "0",
            "source_type": "human",
            "cyclomatic_complexity": 5,
            "halstead_volume": 100.5,
            "halstead_components": {"N": 10, "n": 5, "L": 20, "D": 2, "E": 50},
            "pass_rate": 1,
            "branch_coverage_pct": 85.0
        },
        {
            "task_id": "0",
            "source_type": "codegen-350M",
            "cyclomatic_complexity": 6,
            "halstead_volume": 110.2,
            "halstead_components": {"N": 12, "n": 6, "L": 22, "D": 3, "E": 55},
            "pass_rate": 0,
            "branch_coverage_pct": 70.0
        }
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.json")
        output_path = os.path.join(tmpdir, "output.json")
        
        with open(input_path, 'w') as f:
            json.dump(input_data, f)
        
        aggregate_metrics_to_json(input_path, output_path)
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            result = json.load(f)
        
        assert len(result) == 2
        for record in result:
            assert 'task_id' in record
            assert 'source_type' in record
            assert 'cyclomatic_complexity' in record
            assert 'halstead_volume' in record
            assert 'branch_coverage_pct' in record
            assert 'pass_rate' in record
            assert record['cyclomatic_complexity'] is not None
            assert record['halstead_volume'] is not None

def test_exclusion_gate_null_coverage():
    """Test that pairs with null coverage are excluded."""
    input_data = [
        {
            "task_id": "0",
            "source_type": "human",
            "branch_coverage_pct": 85.0,
            "cyclomatic_complexity": 5,
            "halstead_volume": 100.0
        },
        {
            "task_id": "0",
            "source_type": "codegen-350M",
            "branch_coverage_pct": None,  # Null coverage
            "cyclomatic_complexity": 6,
            "halstead_volume": 110.0
        },
        {
            "task_id": "1",
            "source_type": "human",
            "branch_coverage_pct": 90.0,
            "cyclomatic_complexity": 4,
            "halstead_volume": 90.0
        },
        {
            "task_id": "1",
            "source_type": "codegen-350M",
            "branch_coverage_pct": 80.0,
            "cyclomatic_complexity": 5,
            "halstead_volume": 95.0
        }
    ]
    
    filtered, excluded = apply_pairwise_exclusion_gate(input_data)
    
    # Task 0 should be excluded
    assert "0" in excluded
    # Task 1 should be included
    assert "1" not in excluded
    # Filtered should only contain task 1 records
    assert len(filtered) == 2
    assert all(r['task_id'] == "1" for r in filtered)
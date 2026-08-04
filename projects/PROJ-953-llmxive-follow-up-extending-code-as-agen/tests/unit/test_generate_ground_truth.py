import pytest
import os
import csv
import json
from pathlib import Path
import tempfile
import shutil

# Import the function to test
from scripts.generate_ground_truth import generate_ground_truth, load_baseline_results, load_ingested_tasks

@pytest.fixture
def temp_dirs():
    """Create temporary directories for test artifacts."""
    temp_root = tempfile.mkdtemp()
    data_dir = Path(temp_root) / "data" / "processed"
    data_dir.mkdir(parents=True)
    baseline_dir = data_dir / "baseline_results"
    baseline_dir.mkdir()
    yield {
        "root": Path(temp_root),
        "data": data_dir,
        "baseline": baseline_dir,
        "ingested": data_dir / "ingested_tasks.csv",
        "output": data_dir / "ground_truth.csv"
    }
    shutil.rmtree(temp_root)

def test_generate_ground_truth_success(temp_dirs):
    """Test successful generation of ground truth with mixed outcomes."""
    # Create mock ingested tasks
    tasks_data = [
        {"task_id": "task_001", "code_diff": "diff content 1", "source": "swe-bench"},
        {"task_id": "task_002", "code_diff": "diff content 2", "source": "agent-bench"},
        {"task_id": "task_003", "code_diff": "", "source": "swe-bench"},  # Unparseable
    ]
    
    with open(temp_dirs["ingested"], 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "code_diff", "source"])
        writer.writeheader()
        writer.writerows(tasks_data)
    
    # Create mock baseline results
    baseline_results = {
        "task_001": {"status": "Pass", "duration": 1.5, "error": ""},
        "task_002": {"status": "Fail", "duration": 2.3, "error": "AssertionError"},
        # task_003 has no baseline result (unparseable)
    }
    
    for task_id, data in baseline_results.items():
        result_file = temp_dirs["baseline"] / f"{task_id}.json"
        with open(result_file, 'w') as f:
            json.dump(data, f)
    
    # Run generation
    generate_ground_truth(
        ingested_tasks_path=str(temp_dirs["ingested"]),
        baseline_results_path=str(temp_dirs["baseline"]),
        output_path=str(temp_dirs["output"])
    )
    
    # Verify output
    assert temp_dirs["output"].exists()
    with open(temp_dirs["output"], 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 3
    
    # Check specific outcomes
    outcomes = {row["task_id"]: row["dynamic_execution_outcome"] for row in rows}
    assert outcomes["task_001"] == "Pass"
    assert outcomes["task_002"] == "Fail"
    assert outcomes["task_003"] == "Unparseable"  # Handled correctly

def test_generate_ground_truth_missing_baseline(temp_dirs):
    """Test handling of tasks with missing baseline results."""
    tasks_data = [
        {"task_id": "task_missing", "code_diff": "some diff", "source": "swe-bench"},
    ]
    
    with open(temp_dirs["ingested"], 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "code_diff", "source"])
        writer.writeheader()
        writer.writerows(tasks_data)
    
    # No baseline results created for task_missing
    
    generate_ground_truth(
        ingested_tasks_path=str(temp_dirs["ingested"]),
        baseline_results_path=str(temp_dirs["baseline"]),
        output_path=str(temp_dirs["output"])
    )
    
    with open(temp_dirs["output"], 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 1
    assert rows[0]["dynamic_execution_outcome"] == "Missing_Baseline"

def test_load_baseline_results(temp_dirs):
    """Test loading baseline results from JSON files."""
    # Create mock results
    results_data = {
        "task_a": {"status": "Timeout", "duration": 30.0, "error": "TimeoutError"},
        "task_b": {"status": "Pass", "duration": 0.5, "error": ""},
    }
    
    for task_id, data in results_data.items():
        with open(temp_dirs["baseline"] / f"{task_id}.json", 'w') as f:
            json.dump(data, f)
    
    results = load_baseline_results(str(temp_dirs["baseline"]))
    
    assert "task_a" in results
    assert results["task_a"].status == "Timeout"
    assert results["task_b"].status == "Pass"

def test_load_ingested_tasks(temp_dirs):
    """Test loading ingested tasks from CSV."""
    tasks_data = [
        {"task_id": "t1", "code_diff": "diff1", "source": "swe-bench"},
        {"task_id": "t2", "code_diff": "diff2", "source": "agent-bench"},
    ]
    
    with open(temp_dirs["ingested"], 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "code_diff", "source"])
        writer.writeheader()
        writer.writerows(tasks_data)
    
    tasks = load_ingested_tasks(str(temp_dirs["ingested"]))
    
    assert len(tasks) == 2
    assert tasks[0]["task_id"] == "t1"
    assert tasks[1]["source"] == "agent-bench"

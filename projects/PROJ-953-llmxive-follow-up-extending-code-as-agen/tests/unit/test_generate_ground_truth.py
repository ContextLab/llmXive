import os
import csv
import json
import tempfile
from pathlib import Path
import pytest

from scripts.generate_ground_truth import (
    load_baseline_results,
    load_ingested_tasks,
    process_unparseable_tasks,
    generate_ground_truth
)

def test_load_baseline_results_valid():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"task_1": "Pass", "task_2": "Fail"}, f)
        temp_path = f.name
    
    try:
        results = load_baseline_results(temp_path)
        assert results["task_1"] == "Pass"
        assert results["task_2"] == "Fail"
    finally:
        os.unlink(temp_path)

def test_load_baseline_results_missing_file():
    with pytest.raises(FileNotFoundError):
        load_baseline_results("/nonexistent/path/file.json")

def test_load_ingested_tasks_valid():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.DictWriter(f, fieldnames=['task_id', 'code_diff'])
        writer.writeheader()
        writer.writerow({'task_id': 't1', 'code_diff': 'diff1'})
        writer.writerow({'task_id': 't2', 'code_diff': 'diff2'})
        temp_path = f.name
    
    try:
        tasks = load_ingested_tasks(temp_path)
        assert len(tasks) == 2
        assert tasks[0]['task_id'] == 't1'
    finally:
        os.unlink(temp_path)

def test_process_unparseable_tasks():
    tasks = [
        {'task_id': 't1', 'code_diff': 'diff1', 'status': 'Unparseable'},
        {'task_id': 't2', 'code_diff': 'diff2', 'status': 'Valid'},
        {'task_id': 't3', 'code_diff': 'diff3'} # No status, treated as valid
    ]
    baseline_results = {
        't2': 'Pass',
        't3': 'Timeout/Fail'
    }
    
    processed = process_unparseable_tasks(tasks, baseline_results)
    
    # Check Unparseable task
    unparseable = [t for t in processed if t['task_id'] == 't1'][0]
    assert unparseable['status'] == 'Unparseable'
    assert unparseable['dynamic_execution_outcome'] == 'N/A'
    
    # Check Valid task with outcome
    valid_pass = [t for t in processed if t['task_id'] == 't2'][0]
    assert valid_pass['status'] == 'Valid'
    assert valid_pass['dynamic_execution_outcome'] == 'Pass'
    
    # Check Valid task with timeout
    valid_timeout = [t for t in processed if t['task_id'] == 't3'][0]
    assert valid_timeout['dynamic_execution_outcome'] == 'Timeout/Fail'

def test_generate_ground_truth_integration():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create ingested CSV
        ingested_path = tmpdir / "ingested.csv"
        with open(ingested_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['task_id', 'code_diff', 'status'])
            writer.writeheader()
            writer.writerow({'task_id': 't1', 'code_diff': 'diff1', 'status': 'Unparseable'})
            writer.writerow({'task_id': 't2', 'code_diff': 'diff2', 'status': 'Valid'})
            writer.writerow({'task_id': 't3', 'code_diff': 'diff3', 'status': 'Valid'})
        
        # Create baseline JSON
        baseline_path = tmpdir / "baseline.json"
        with open(baseline_path, 'w') as f:
            json.dump({
                't2': 'Pass',
                't3': 'Timeout/Fail'
            }, f)
        
        output_path = tmpdir / "ground_truth.csv"
        
        generate_ground_truth(str(ingested_path), str(baseline_path), str(output_path))
        
        # Verify output
        assert output_path.exists()
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 3
        
        # Check specific rows
        t1 = next(r for r in rows if r['task_id'] == 't1')
        assert t1['status'] == 'Unparseable'
        assert t1['dynamic_execution_outcome'] == 'N/A'
        
        t2 = next(r for r in rows if r['task_id'] == 't2')
        assert t2['status'] == 'Valid'
        assert t2['dynamic_execution_outcome'] == 'Pass'
        
        t3 = next(r for r in rows if r['task_id'] == 't3')
        assert t3['status'] == 'Valid'
        assert t3['dynamic_execution_outcome'] == 'Timeout/Fail'
import pytest
import csv
import tempfile
import os
from pathlib import Path
from scripts.generate_ground_truth import process_unparseable_tasks, generate_ground_truth

def test_process_unparseable_tasks_syntax_error():
    """Test that tasks with syntax errors are flagged as Unparseable."""
    tasks = [
        {
            'task_id': 'task_1',
            'original_code': 'def valid(): pass',
            'code_diff': 'diff...'
        },
        {
            'task_id': 'task_2',
            'original_code': 'def invalid(:', # Syntax error
            'code_diff': 'diff...'
        },
        {
            'task_id': 'task_3',
            'original_code': '',
            'code_diff': ''
        }
    ]

    result = process_unparseable_tasks(tasks)

    # Task 1 should be valid (or Pending if no baseline result yet)
    assert result[0]['dynamic_execution_outcome'] != 'Unparseable'
    
    # Task 2 should be flagged Unparseable
    assert result[1]['dynamic_execution_outcome'] == 'Unparseable'
    assert 'parse_error' in result[1]
    
    # Task 3 (empty) should be flagged Unparseable
    assert result[2]['dynamic_execution_outcome'] == 'Unparseable'

def test_process_unparseable_tasks_retains_row():
    """Test that unparseable tasks are retained in the list, not dropped."""
    tasks = [
        {
            'task_id': 'task_bad',
            'original_code': 'syntax error here',
            'code_diff': 'diff'
        }
    ]
    result = process_unparseable_tasks(tasks)
    assert len(result) == 1
    assert result[0]['task_id'] == 'task_bad'
    assert result[0]['dynamic_execution_outcome'] == 'Unparseable'

def test_generate_ground_truth_integration():
    """Integration test for generating ground truth with unparseable tasks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ingested_path = Path(tmpdir) / 'ingested.csv'
        baseline_path = Path(tmpdir) / 'baseline.json'
        output_path = Path(tmpdir) / 'ground_truth.csv'

        # Create mock ingested data
        with open(ingested_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['task_id', 'original_code', 'code_diff'])
            writer.writeheader()
            writer.writerow({'task_id': 'good_1', 'original_code': 'x = 1', 'code_diff': 'diff'})
            writer.writerow({'task_id': 'bad_1', 'original_code': 'x =', 'code_diff': 'diff'})

        # Create empty baseline results
        with open(baseline_path, 'w') as f:
            f.write('{}')

        generate_ground_truth(str(ingested_path), str(baseline_path), str(output_path))

        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        
        good_row = next(r for r in rows if r['task_id'] == 'good_1')
        bad_row = next(r for r in rows if r['task_id'] == 'bad_1')

        assert good_row['dynamic_execution_outcome'] != 'Unparseable'
        assert bad_row['dynamic_execution_outcome'] == 'Unparseable'
        assert 'parse_error' in bad_row

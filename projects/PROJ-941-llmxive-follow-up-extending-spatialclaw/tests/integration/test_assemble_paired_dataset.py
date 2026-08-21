"""
Integration test for T047: Final Paired Dataset Assembly.

Tests the assembly of the final paired dataset by:
1. Creating mock baseline and 2D agent results
2. Running the assembly script
3. Verifying the output CSV schema and content
"""

import os
import json
import csv
import tempfile
import shutil
import pytest
from pathlib import Path

# Import the module to test
import sys
sys.path.insert(0, 'code')
from analysis.assemble_paired_dataset import (
    load_baseline_results,
    load_2d_run_results,
    aggregate_2d_results,
    build_paired_dataset,
    write_csv,
    verify_no_nulls
)


class TestAssemblePairedDataset:

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)

    @pytest.fixture
    def mock_baseline_data(self):
        """Create mock baseline results."""
        return [
            {
                'task_id': 'task_001',
                'task_type': 'occlusion',
                'success': True,
                'latency_ms': 100.5,
                'wall_clock_time_ms': 105.0
            },
            {
                'task_id': 'task_002',
                'task_type': 'depth',
                'success': False,
                'latency_ms': 200.0,
                'wall_clock_time_ms': 210.0
            },
            {
                'task_id': 'task_003',
                'task_type': 'relative',
                'success': True,
                'latency_ms': 150.0,
                'wall_clock_time_ms': 160.0
            }
        ]

    @pytest.fixture
    def mock_2d_runs(self):
        """Create mock 2D agent run results (5 runs per task)."""
        runs = []
        for task_id in ['task_001', 'task_002', 'task_003']:
            for run_idx in range(5):
                runs.append({
                    'task_id': task_id,
                    'task_type': 'occlusion' if task_id == 'task_001' else ('depth' if task_id == 'task_002' else 'relative'),
                    'success': run_idx < 4,  # 4/5 successes
                    'latency_ms': 120.0 + run_idx,
                    'run_id': run_idx
                })
        return runs

    def test_load_baseline_results_from_list(self, temp_dir, mock_baseline_data):
        """Test loading baseline results from a JSON list."""
        baseline_path = os.path.join(temp_dir, 'baseline.json')
        with open(baseline_path, 'w') as f:
            json.dump(mock_baseline_data, f)

        result = load_baseline_results(baseline_path)
        assert len(result) == 3
        assert 'task_001' in result
        assert result['task_001']['success'] is True

    def test_load_baseline_results_from_dict(self, temp_dir, mock_baseline_data):
        """Test loading baseline results from a JSON dict."""
        baseline_dict = {item['task_id']: item for item in mock_baseline_data}
        baseline_path = os.path.join(temp_dir, 'baseline_dict.json')
        with open(baseline_path, 'w') as f:
            json.dump(baseline_dict, f)

        result = load_baseline_results(baseline_path)
        assert len(result) == 3
        assert result['task_001']['success'] is True

    def test_load_2d_run_results(self, temp_dir, mock_2d_runs):
        """Test loading 2D agent run results from multiple files."""
        runs_dir = os.path.join(temp_dir, 'runs')
        os.makedirs(runs_dir)

        # Write each run to a separate file
        for i, run in enumerate(mock_2d_runs):
            filepath = os.path.join(runs_dir, f'run_{i}.json')
            with open(filepath, 'w') as f:
                json.dump(run, f)

        result = load_2d_run_results(runs_dir)
        assert len(result) == 3  # 3 tasks
        assert len(result['task_001']) == 5  # 5 runs per task

    def test_aggregate_2d_results(self, temp_dir, mock_2d_runs):
        """Test aggregation of 2D results."""
        runs_dir = os.path.join(temp_dir, 'runs')
        os.makedirs(runs_dir)

        for i, run in enumerate(mock_2d_runs):
            filepath = os.path.join(runs_dir, f'run_{i}.json')
            with open(filepath, 'w') as f:
                json.dump(run, f)

        task_runs = load_2d_run_results(runs_dir)
        aggregated = aggregate_2d_results(task_runs)

        # Check task_001: 4/5 successes = 0.8
        assert aggregated['task_001']['2d_success_rate'] == 0.8
        # Check mean latency: (120+121+122+123+124)/5 = 122.0
        assert aggregated['task_001']['2d_mean_latency'] == 122.0

    def test_build_paired_dataset(self, mock_baseline_data, mock_2d_runs):
        """Test building the paired dataset."""
        baseline_dict = {item['task_id']: item for item in mock_baseline_data}

        # Create temp dir for 2D runs
        temp_dir = tempfile.mkdtemp()
        runs_dir = os.path.join(temp_dir, 'runs')
        os.makedirs(runs_dir)

        for i, run in enumerate(mock_2d_runs):
            filepath = os.path.join(runs_dir, f'run_{i}.json')
            with open(filepath, 'w') as f:
                json.dump(run, f)

        task_runs = load_2d_run_results(runs_dir)
        aggregated_2d = aggregate_2d_results(task_runs)

        paired = build_paired_dataset(baseline_dict, aggregated_2d)

        assert len(paired) == 3
        # Check sorting by task_id
        assert paired[0]['task_id'] == 'task_001'
        assert paired[1]['task_id'] == 'task_002'
        assert paired[2]['task_id'] == 'task_003'

        # Check calculations for task_001
        row = paired[0]
        assert row['2d_success_rate'] == 0.8
        assert row['3d_success'] == 1  # True -> 1
        assert row['success_diff'] == -0.2  # 0.8 - 1.0

        shutil.rmtree(temp_dir)

    def test_write_csv_and_verify(self, temp_dir, mock_baseline_data, mock_2d_runs):
        """Test writing CSV and verifying no nulls."""
        baseline_dict = {item['task_id']: item for item in mock_baseline_data}

        runs_dir = os.path.join(temp_dir, 'runs')
        os.makedirs(runs_dir)

        for i, run in enumerate(mock_2d_runs):
            filepath = os.path.join(runs_dir, f'run_{i}.json')
            with open(filepath, 'w') as f:
                json.dump(run, f)

        task_runs = load_2d_run_results(runs_dir)
        aggregated_2d = aggregate_2d_results(task_runs)
        paired = build_paired_dataset(baseline_dict, aggregated_2d)

        output_path = os.path.join(temp_dir, 'output.csv')
        write_csv(paired, output_path)

        # Verify file exists and has content
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 3

            # Verify schema
            expected_cols = ['task_id', 'task_type', '2d_success_rate', '2d_mean_latency',
                             '3d_success', '3d_latency', 'success_diff', 'latency_diff']
            assert list(rows[0].keys()) == expected_cols

            # Verify no nulls
            assert verify_no_nulls(rows, ['task_id', '2d_success_rate', '3d_success']) is True

    def test_missing_baseline_task(self, temp_dir):
        """Test handling of task in 2D but not in baseline."""
        baseline_dict = {'task_001': {'task_id': 'task_001', 'task_type': 'occlusion', 'success': True, 'latency_ms': 100}}

        task_runs = {
            'task_001': [{'task_id': 'task_001', 'task_type': 'occlusion', 'success': True, 'latency_ms': 110}],
            'task_002': [{'task_id': 'task_002', 'task_type': 'depth', 'success': False, 'latency_ms': 200}]  # Not in baseline
        }

        aggregated_2d = aggregate_2d_results(task_runs)
        paired = build_paired_dataset(baseline_dict, aggregated_2d)

        assert len(paired) == 2
        # task_002 should have 0 for baseline values
        task_002_row = next(r for r in paired if r['task_id'] == 'task_002')
        assert task_002_row['3d_success'] == 0
        assert task_002_row['3d_latency'] == 0

    def test_missing_2d_runs(self, temp_dir, mock_baseline_data):
        """Test handling of task in baseline but not in 2D runs."""
        baseline_dict = {item['task_id']: item for item in mock_baseline_data}

        task_runs = {
            'task_001': [{'task_id': 'task_001', 'task_type': 'occlusion', 'success': True, 'latency_ms': 110}]
            # task_002 and task_003 missing
        }

        aggregated_2d = aggregate_2d_results(task_runs)
        paired = build_paired_dataset(baseline_dict, aggregated_2d)

        assert len(paired) == 3
        # task_002 should have 0 for 2D values
        task_002_row = next(r for r in paired if r['task_id'] == 'task_002')
        assert task_002_row['2d_success_rate'] == 0.0
        assert task_002_row['2d_mean_latency'] == 0.0
"""
Integration tests for final paired dataset assembly.

Tests the complete flow of merging 2D and 3D results into a single CSV.
"""

import os
import json
import csv
import tempfile
import shutil
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.assemble_paired_dataset import (
    load_baseline_results,
    load_2d_run_results,
    aggregate_2d_results,
    build_paired_dataset,
    write_csv,
    main
)


class TestAssemblePairedDataset:
    """Test suite for paired dataset assembly."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test artifacts."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)

    @pytest.fixture
    def sample_baseline_data(self):
        """Generate sample baseline data."""
        return [
            {
                'task_id': 'task_001',
                'task_type': 'occlusion',
                'success': True,
                'latency_ms': 120.5
            },
            {
                'task_id': 'task_002',
                'task_type': 'depth',
                'success': False,
                'latency_ms': 150.0
            },
            {
                'task_id': 'task_003',
                'task_type': 'relative',
                'success': True,
                'latency_ms': 110.0
            }
        ]

    @pytest.fixture
    def sample_2d_run_data(self):
        """Generate sample 2D run data (multiple runs per task)."""
        return [
            # Run 1
            [
                {'task_id': 'task_001', 'task_type': 'occlusion', 'success': True, 'latency_ms': 130.0},
                {'task_id': 'task_002', 'task_type': 'depth', 'success': False, 'latency_ms': 160.0},
                {'task_id': 'task_003', 'task_type': 'relative', 'success': True, 'latency_ms': 115.0}
            ],
            # Run 2
            [
                {'task_id': 'task_001', 'task_type': 'occlusion', 'success': True, 'latency_ms': 125.0},
                {'task_id': 'task_002', 'task_type': 'depth', 'success': True, 'latency_ms': 155.0},
                {'task_id': 'task_003', 'task_type': 'relative', 'success': False, 'latency_ms': 112.0}
            ],
            # Run 3
            [
                {'task_id': 'task_001', 'task_type': 'occlusion', 'success': False, 'latency_ms': 140.0},
                {'task_id': 'task_002', 'task_type': 'depth', 'success': False, 'latency_ms': 170.0},
                {'task_id': 'task_003', 'task_type': 'relative', 'success': True, 'latency_ms': 108.0}
            ]
        ]

    def test_load_baseline_results(self, temp_dir, sample_baseline_data):
        """Test loading baseline results from JSON."""
        baseline_path = os.path.join(temp_dir, 'baseline.json')
        with open(baseline_path, 'w') as f:
            json.dump(sample_baseline_data, f)

        results = load_baseline_results(baseline_path)

        assert len(results) == 3
        assert 'task_001' in results
        assert results['task_001']['success'] is True
        assert results['task_001']['latency_ms'] == 120.5

    def test_load_2d_run_results(self, temp_dir, sample_2d_run_data):
        """Test loading multiple 2D run results."""
        runs_dir = os.path.join(temp_dir, 'runs')
        os.makedirs(runs_dir)

        for i, run_data in enumerate(sample_2d_run_data):
            run_path = os.path.join(runs_dir, f'run_{i}.json')
            with open(run_path, 'w') as f:
                json.dump(run_data, f)

        results = load_2d_run_results(runs_dir)

        assert len(results) == 3
        assert len(results['task_001']) == 3
        assert len(results['task_002']) == 3

    def test_aggregate_2d_results(self, sample_2d_run_data):
        """Test aggregation of 2D results across runs."""
        raw_results = {}
        for run_data in sample_2d_run_data:
            for item in run_data:
                task_id = item['task_id']
                if task_id not in raw_results:
                    raw_results[task_id] = []
                raw_results[task_id].append(item)

        aggregated = aggregate_2d_results(raw_results)

        # task_001: 2/3 success, mean latency (130+125+140)/3 = 131.67
        assert aggregated['task_001']['2d_success_rate'] == pytest.approx(2/3, rel=0.01)
        assert aggregated['task_001']['2d_mean_latency'] == pytest.approx(131.67, rel=0.01)
        assert aggregated['task_001']['n_runs'] == 3

    def test_build_paired_dataset(self, sample_baseline_data, sample_2d_run_data):
        """Test building the paired dataset."""
        # Load and aggregate 2D
        raw_2d = {}
        for run_data in sample_2d_run_data:
            for item in run_data:
                task_id = item['task_id']
                if task_id not in raw_2d:
                    raw_2d[task_id] = []
                raw_2d[task_id].append(item)
        aggregated_2d = aggregate_2d_results(raw_2d)

        # Load baseline
        baseline_dict = {item['task_id']: item for item in sample_baseline_data}

        # Build paired
        paired = build_paired_dataset(aggregated_2d, baseline_dict)

        assert len(paired) == 3
        assert paired[0]['task_id'] == 'task_001'
        assert 'success_diff' in paired[0]
        assert 'latency_diff' in paired[0]

        # Verify sorting
        task_ids = [p['task_id'] for p in paired]
        assert task_ids == sorted(task_ids)

    def test_write_csv(self, temp_dir, sample_baseline_data, sample_2d_run_data):
        """Test writing the paired dataset to CSV."""
        # Load and aggregate
        raw_2d = {}
        for run_data in sample_2d_run_data:
            for item in run_data:
                task_id = item['task_id']
                if task_id not in raw_2d:
                    raw_2d[task_id] = []
                raw_2d[task_id].append(item)
        aggregated_2d = aggregate_2d_results(raw_2d)
        baseline_dict = {item['task_id']: item for item in sample_baseline_data}

        paired = build_paired_dataset(aggregated_2d, baseline_dict)

        output_path = os.path.join(temp_dir, 'paired_dataset.csv')
        write_csv(paired, output_path)

        assert os.path.exists(output_path)

        # Verify CSV content
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 3
        assert set(rows[0].keys()) == {
            'task_id', 'task_type', '2d_success_rate', '2d_mean_latency',
            '3d_success', '3d_latency', 'success_diff', 'latency_diff'
        }

    def test_null_value_check(self, temp_dir):
        """Test that null values in critical columns raise an error."""
        paired_data = [
            {
                'task_id': 'task_001',
                'task_type': 'occlusion',
                '2d_success_rate': 0.5,
                '2d_mean_latency': 100.0,
                '3d_success': True,
                '3d_latency': 120.0,
                'success_diff': -0.5,
                'latency_diff': -20.0
            },
            {
                'task_id': 'task_002',
                'task_type': None,  # Null task_type
                '2d_success_rate': 0.5,
                '2d_mean_latency': 100.0,
                '3d_success': True,
                '3d_latency': 120.0,
                'success_diff': -0.5,
                'latency_diff': -20.0
            }
        ]

        output_path = os.path.join(temp_dir, 'paired_dataset.csv')

        with pytest.raises(ValueError, match="Null value found in critical column"):
            write_csv(paired_data, output_path)

    def test_missing_task_handling(self, temp_dir, sample_baseline_data):
        """Test handling of tasks missing in one of the datasets."""
        # Create 2D data with only 2 tasks
        raw_2d = {
            'task_001': [{'task_id': 'task_001', 'task_type': 'occlusion', 'success': True, 'latency_ms': 130.0}],
            'task_002': [{'task_id': 'task_002', 'task_type': 'depth', 'success': False, 'latency_ms': 160.0}]
        }
        aggregated_2d = aggregate_2d_results(raw_2d)
        baseline_dict = {item['task_id']: item for item in sample_baseline_data}

        paired = build_paired_dataset(aggregated_2d, baseline_dict)

        # Should only have 2 tasks (task_003 is missing from 2D)
        assert len(paired) == 2
        assert 'task_003' not in [p['task_id'] for p in paired]
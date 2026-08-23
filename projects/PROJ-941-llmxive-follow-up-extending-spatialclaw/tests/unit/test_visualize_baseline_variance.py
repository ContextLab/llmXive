"""
Unit tests for T063: Baseline Variance Visualization.
"""
import os
import sys
import json
import tempfile
import csv
import pytest
import numpy as np

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from stats.visualize_baseline_variance import (
    load_paired_dataset,
    load_baseline_runs_json,
    calculate_statistics,
    generate_plot
)

class TestLoadPairedDataset:
    def test_load_valid_csv(self, tmp_path):
        csv_path = tmp_path / "test.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['task_id', '3d_latency', '3d_success'])
            writer.writeheader()
            writer.writerow({'task_id': '1', '3d_latency': '100.5', '3d_success': '1.0'})
            writer.writerow({'task_id': '2', '3d_latency': '102.0', '3d_success': '0.0'})

        data = load_paired_dataset(str(csv_path))
        assert len(data) == 2
        assert data[0]['3d_latency'] == '100.5'

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_paired_dataset(str(tmp_path / "nonexistent.csv"))

class TestLoadBaselineRunsJson:
    def test_load_valid_json(self, tmp_path):
        json_path = tmp_path / "baseline_run_1.json"
        with open(json_path, 'w') as f:
            json.dump({'latency_ms': 100.5, 'success': 1.0}, f)

        runs = load_baseline_runs_json(str(tmp_path))
        assert len(runs) == 1
        assert runs[0]['latency_ms'] == 100.5

    def test_no_files(self, tmp_path):
        runs = load_baseline_runs_json(str(tmp_path))
        assert len(runs) == 0

class TestCalculateStatistics:
    def test_calculate_with_data(self):
        data = [
            {'3d_latency': '100.0', '3d_success': '1.0'},
            {'3d_latency': '200.0', '3d_success': '0.0'},
            {'3d_latency': '150.0', '3d_success': '1.0'}
        ]
        stats = calculate_statistics(data)
        
        assert stats['latency'] is not None
        assert stats['latency']['count'] == 3
        assert stats['latency']['mean'] == 150.0
        
        assert stats['success'] is not None
        assert stats['success']['mean'] == 2.0 / 3.0

    def test_calculate_empty(self):
        stats = calculate_statistics([])
        assert stats['latency'] is None
        assert stats['success'] is None

class TestGeneratePlot:
    def test_plot_generation(self, tmp_path):
        paired_data = [
            {'3d_latency': '100.0', '3d_success': '1.0'},
            {'3d_latency': '105.0', '3d_success': '1.0'},
            {'3d_latency': '95.0', '3d_success': '1.0'}
        ]
        baseline_runs = []
        output_path = str(tmp_path / "plot.png")

        generate_plot(paired_data, baseline_runs, output_path)

        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0

    def test_plot_with_baseline_runs(self, tmp_path):
        paired_data = []
        baseline_runs = [
            {'latency_ms': 100.0, 'success': 1.0},
            {'latency_ms': 102.0, 'success': 1.0},
            {'latency_ms': 98.0, 'success': 1.0}
        ]
        output_path = str(tmp_path / "plot.png")

        generate_plot(paired_data, baseline_runs, output_path)

        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
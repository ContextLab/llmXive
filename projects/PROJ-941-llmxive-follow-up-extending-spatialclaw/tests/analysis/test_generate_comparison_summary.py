"""
Tests for T025: generate_comparison_summary.py
"""

import csv
import os
import tempfile
import pytest
from unittest.mock import patch, mock_open

# Import the module under test
import sys
sys.path.insert(0, 'code')
from analysis.generate_comparison_summary import (
    load_comparison_results,
    aggregate_by_task_type,
    write_summary_csv
)


class TestLoadComparisonResults:
    def test_load_valid_csv(self, tmp_path):
        """Test loading a valid CSV file."""
        csv_content = """task_id,task_type,success_flag,wall_clock_time_ms,agent_type
        task_1,occlusion,1.0,100.5,2D
        task_2,depth,0.0,200.0,3D
        """
        input_file = tmp_path / "input.csv"
        input_file.write_text(csv_content)

        results = load_comparison_results(str(input_file))
        assert len(results) == 2
        assert results[0]['task_type'] == 'occlusion'
        assert results[0]['success_flag'] == 1.0
        assert results[1]['agent_type'] == '3D'

    def test_load_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_comparison_results(str(tmp_path / "nonexistent.csv"))

    def test_load_null_success_flag_handling(self, tmp_path):
        """Test that rows with null success_flag are parsed but kept for filtering."""
        csv_content = """task_id,task_type,success_flag,wall_clock_time_ms,agent_type
        task_1,occlusion,,50.0,2D
        task_2,depth,1.0,60.0,3D
        """
        input_file = tmp_path / "input.csv"
        input_file.write_text(csv_content)

        results = load_comparison_results(str(input_file))
        assert len(results) == 2
        assert results[0]['success_flag'] is None
        assert results[1]['success_flag'] == 1.0


class TestAggregateByTaskType:
    def test_aggregate_success_and_time(self):
        """Test aggregation logic for mean success and mean time."""
        data = [
            {'task_id': 't1', 'task_type': 'occlusion', 'success_flag': 1.0, 'wall_clock_time_ms': 100.0, 'agent_type': '2D'},
            {'task_id': 't2', 'task_type': 'occlusion', 'success_flag': 0.0, 'wall_clock_time_ms': 200.0, 'agent_type': '2D'},
            {'task_id': 't3', 'task_type': 'depth', 'success_flag': 1.0, 'wall_clock_time_ms': 300.0, 'agent_type': '3D'},
        ]

        summary = aggregate_by_task_type(data)

        # Should have 2 rows: (occlusion, 2D) and (depth, 3D)
        assert len(summary) == 2

        # Find occlusion row
        occlusion_row = next(r for r in summary if r['task_type'] == 'occlusion' and r['agent_type'] == '2D')
        assert occlusion_row['success_flag'] == 0.5  # (1.0 + 0.0) / 2
        assert occlusion_row['wall_clock_time_ms'] == 150.0  # (100 + 200) / 2

        # Find depth row
        depth_row = next(r for r in summary if r['task_type'] == 'depth' and r['agent_type'] == '3D')
        assert depth_row['success_flag'] == 1.0
        assert depth_row['wall_clock_time_ms'] == 300.0

    def test_exclude_null_success_flag(self):
        """Test that rows with null success_flag are excluded from aggregation."""
        data = [
            {'task_id': 't1', 'task_type': 'occlusion', 'success_flag': 1.0, 'wall_clock_time_ms': 100.0, 'agent_type': '2D'},
            {'task_id': 't2', 'task_type': 'occlusion', 'success_flag': None, 'wall_clock_time_ms': 200.0, 'agent_type': '2D'}, # Should be excluded
        ]

        summary = aggregate_by_task_type(data)

        # Only 1 row expected
        assert len(summary) == 1
        assert summary[0]['success_flag'] == 1.0
        assert summary[0]['wall_clock_time_ms'] == 100.0

    def test_empty_input(self):
        """Test aggregation with empty list."""
        summary = aggregate_by_task_type([])
        assert summary == []


class TestWriteSummaryCsv:
    def test_write_csv_creates_file(self, tmp_path):
        """Test that write_summary_csv creates the file with correct headers."""
        output_file = tmp_path / "summary.csv"
        data = [
            {'task_id': 'AGGREGATE', 'task_type': 'occlusion', 'success_flag': 0.5, 'wall_clock_time_ms': 150.0, 'agent_type': '2D'}
        ]

        write_summary_csv(data, str(output_file))

        assert output_file.exists()
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['task_id'] == 'AGGREGATE'
            assert rows[0]['task_type'] == 'occlusion'
            assert rows[0]['success_flag'] == '0.5'
            assert rows[0]['agent_type'] == '2D'

    def test_creates_directory(self, tmp_path):
        """Test that the function creates the output directory if it doesn't exist."""
        nested_dir = tmp_path / "results" / "analysis"
        output_file = nested_dir / "summary.csv"
        data = []

        write_summary_csv(data, str(output_file))

        assert nested_dir.exists()
        assert output_file.exists()
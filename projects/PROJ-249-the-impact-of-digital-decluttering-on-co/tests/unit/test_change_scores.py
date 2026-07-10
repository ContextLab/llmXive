"""
Unit tests for change score calculation (T035).

Tests FR-005: Change score calculator functionality.
"""

import pytest
import os
import csv
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

from code.analysis.change_scores import (
    calculate_change_score,
    calculate_change_scores_for_participant,
    load_merged_data,
    write_change_scores,
    run_change_score_calculation,
    ChangeScoreResult,
    get_metric_mapping
)


class TestCalculateChangeScore:
    """Tests for the calculate_change_score helper function."""

    def test_positive_change(self):
        """Test calculation when post > baseline."""
        change, percent, direction = calculate_change_score(10.0, 15.0)
        assert change == 5.0
        assert abs(percent - 50.0) < 0.01  # 5/10 * 100
        assert direction == 'increase'

    def test_negative_change(self):
        """Test calculation when post < baseline."""
        change, percent, direction = calculate_change_score(20.0, 15.0)
        assert change == -5.0
        assert abs(percent - (-25.0)) < 0.01  # -5/20 * 100
        assert direction == 'decrease'

    def test_no_change(self):
        """Test calculation when post == baseline."""
        change, percent, direction = calculate_change_score(10.0, 10.0)
        assert change == 0.0
        assert percent == 0.0
        assert direction == 'no_change'

    def test_missing_baseline(self):
        """Test handling of missing baseline."""
        change, percent, direction = calculate_change_score(None, 10.0)
        assert change is None
        assert percent is None
        assert direction == 'missing'

    def test_missing_post(self):
        """Test handling of missing post."""
        change, percent, direction = calculate_change_score(10.0, None)
        assert change is None
        assert percent is None
        assert direction == 'missing'

    def test_both_missing(self):
        """Test handling of both values missing."""
        change, percent, direction = calculate_change_score(None, None)
        assert change is None
        assert percent is None
        assert direction == 'missing'

    def test_zero_baseline(self):
        """Test handling of zero baseline (avoid division by zero)."""
        change, percent, direction = calculate_change_score(0.0, 5.0)
        assert change == 5.0
        assert percent is None  # Cannot calculate percent of zero
        assert direction == 'increase'


class TestCalculateChangeScoresForParticipant:
    """Tests for per-participant change score calculation."""

    @pytest.fixture
    def sample_participant_data(self):
        """Create sample participant data."""
        return {
            'participant_id': 'P001',
            'baseline_sart_errors': 12.0,
            'post_sart_errors': 8.0,
            'baseline_ospan_score': 45.0,
            'post_ospan_score': 52.0,
            'baseline_pss10_score': 25.0,
            'post_pss10_score': 18.0,
            'baseline_panas_positive': 20.0,
            'post_panas_positive': 25.0,
            'baseline_panas_negative': 22.0,
            'post_panas_negative': 15.0,
            'compliance_score': 0.85
        }

    def test_calculate_all_metrics(self, sample_participant_data):
        """Test calculation for all standard metrics."""
        metrics = ['sart_errors', 'ospan_score', 'pss10_score',
                   'panas_positive', 'panas_negative', 'compliance_score']
        results = calculate_change_scores_for_participant(sample_participant_data, metrics)

        assert len(results) == 6
        assert all(r.participant_id == 'P001' for r in results)
        assert all(r.valid for r in results)

        # Check specific changes
        sart_result = next(r for r in results if r.metric_type == 'sart_errors')
        assert sart_result.change_score == -4.0  # 8 - 12
        assert sart_result.direction == 'decrease'

        ospan_result = next(r for r in results if r.metric_type == 'ospan_score')
        assert ospan_result.change_score == 7.0  # 52 - 45
        assert ospan_result.direction == 'increase'

    def test_missing_values(self, sample_participant_data):
        """Test handling of missing values in participant data."""
        sample_participant_data['baseline_sart_errors'] = None
        sample_participant_data['post_ospan_score'] = None

        metrics = ['sart_errors', 'ospan_score']
        results = calculate_change_scores_for_participant(sample_participant_data, metrics)

        sart_result = next(r for r in results if r.metric_type == 'sart_errors')
        assert not sart_result.valid
        assert sart_result.missing_baseline
        assert not sart_result.missing_post

        ospan_result = next(r for r in results if r.metric_type == 'ospan_score')
        assert not ospan_result.valid
        assert not ospan_result.missing_baseline
        assert ospan_result.missing_post


class TestLoadMergedData:
    """Tests for loading merged data."""

    @pytest.fixture
    def temp_csv_file(self, tmp_path):
        """Create a temporary CSV file with merged data."""
        csv_path = tmp_path / 'merged_data.csv'
        data = [
            {'participant_id': 'P001', 'baseline_sart_errors': '10.0', 'post_sart_errors': '8.0'},
            {'participant_id': 'P002', 'baseline_sart_errors': '15.0', 'post_sart_errors': '12.0'},
        ]
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        return str(csv_path)

    def test_load_valid_csv(self, temp_csv_file):
        """Test loading a valid CSV file."""
        data = load_merged_data(temp_csv_file)
        assert len(data) == 2
        assert data[0]['participant_id'] == 'P001'
        assert data[0]['baseline_sart_errors'] == 10.0
        assert data[0]['post_sart_errors'] == 8.0

    def test_load_missing_file(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            load_merged_data('/nonexistent/path/file.csv')

    def test_load_empty_file(self, tmp_path):
        """Test loading an empty CSV (header only)."""
        csv_path = tmp_path / 'empty.csv'
        with open(csv_path, 'w') as f:
            f.write('participant_id,baseline_sart_errors,post_sart_errors\n')

        data = load_merged_data(str(csv_path))
        assert len(data) == 0


class TestWriteChangeScores:
    """Tests for writing change score results."""

    @pytest.fixture
    def sample_results(self):
        """Create sample ChangeScoreResult objects."""
        return [
            ChangeScoreResult(
                participant_id='P001',
                metric_type='sart_errors',
                baseline_value=10.0,
                post_value=8.0,
                change_score=-2.0,
                percent_change=-20.0,
                direction='decrease',
                valid=True
            ),
            ChangeScoreResult(
                participant_id='P001',
                metric_type='ospan_score',
                baseline_value=40.0,
                post_value=45.0,
                change_score=5.0,
                percent_change=12.5,
                direction='increase',
                valid=True
            ),
        ]

    def test_write_csv_and_json(self, sample_results, tmp_path):
        """Test writing results to both CSV and JSON."""
        output_path = str(tmp_path / 'change_scores.csv')
        written_path = write_change_scores(sample_results, output_path)

        # Check CSV exists
        assert os.path.exists(written_path)
        with open(written_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]['participant_id'] == 'P001'
            assert rows[0]['change_score'] == '-2.0'

        # Check JSON exists
        json_path = written_path.replace('.csv', '.json')
        assert os.path.exists(json_path)
        with open(json_path, 'r') as f:
            data = json.load(f)
            assert data['total_participants'] == 1
            assert data['total_metrics'] == 2
            assert data['valid_scores'] == 2


class TestRunChangeScoreCalculation:
    """Tests for the main pipeline function."""

    @pytest.fixture
    def setup_test_data(self, tmp_path):
        """Set up test data directory structure."""
        # Create input file
        input_dir = tmp_path / 'data' / 'processed'
        input_dir.mkdir(parents=True)
        input_file = input_dir / 'merged_data.csv'

        with open(input_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'participant_id', 'baseline_sart_errors', 'post_sart_errors',
                'baseline_ospan_score', 'post_ospan_score'
            ])
            writer.writeheader()
            writer.writerow({
                'participant_id': 'P001',
                'baseline_sart_errors': '12.0',
                'post_sart_errors': '8.0',
                'baseline_ospan_score': '45.0',
                'post_ospan_score': '52.0'
            })

        output_dir = tmp_path / 'output'
        output_dir.mkdir()

        return {
            'input_file': str(input_file),
            'output_dir': str(output_dir)
        }

    def test_run_full_pipeline(self, setup_test_data):
        """Test running the complete change score calculation pipeline."""
        output_file = str(Path(setup_test_data['output_dir']) / 'change_scores.csv')

        results = run_change_score_calculation(
            input_path=setup_test_data['input_file'],
            output_path=output_file,
            metrics=['sart_errors', 'ospan_score']
        )

        assert len(results) == 2  # 2 metrics for 1 participant
        assert os.path.exists(output_file)

        # Verify CSV content
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2

            sart_row = next(r for r in rows if r['metric_type'] == 'sart_errors')
            assert float(sart_row['change_score']) == -4.0

            ospan_row = next(r for r in rows if r['metric_type'] == 'ospan_score')
            assert float(ospan_row['change_score']) == 7.0


class TestGetMetricMapping:
    """Tests for metric mapping function."""

    def test_mapping_contains_expected_metrics(self):
        """Test that the mapping includes all required metrics."""
        mapping = get_metric_mapping()

        expected = ['sart_errors', 'ospan_score', 'pss10_score',
                    'panas_positive', 'panas_negative', 'compliance_score']

        for metric in expected:
            assert metric in mapping
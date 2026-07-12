"""
Unit tests for T024: Summary Statistics generation.
"""
import csv
import json
import os
import tempfile
from pathlib import Path

import pytest

from analysis.summary_statistics import (
    calculate_cohen_d,
    calculate_mean,
    calculate_std,
    generate_summary_statistics,
    run_summary_statistics,
    save_summary_statistics
)


class TestDescriptiveStatistics:
    def test_calculate_mean(self):
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert calculate_mean(values) == 3.0

    def test_calculate_mean_empty(self):
        assert calculate_mean([]) == 0.0

    def test_calculate_std(self):
        values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        std = calculate_std(values)
        assert abs(std - 2.138) < 0.01

    def test_calculate_std_small_sample(self):
        values = [1.0, 2.0]
        std = calculate_std(values)
        assert abs(std - 0.707) < 0.01

    def test_calculate_std_empty(self):
        assert calculate_std([]) == 0.0

class TestCohenD:
    def test_cohen_d_basic(self):
        group1 = [1.0, 2.0, 3.0]
        group2 = [4.0, 5.0, 6.0]
        d = calculate_cohen_d(group1, group2)
        assert d < 0  # group2 is larger, so d should be negative
        assert abs(d) > 1.0  # Large effect

    def test_cohen_d_equal(self):
        group1 = [1.0, 2.0, 3.0]
        group2 = [1.0, 2.0, 3.0]
        d = calculate_cohen_d(group1, group2)
        assert abs(d) < 0.01

    def test_cohen_d_small_sample(self):
        group1 = [1.0, 2.0]
        group2 = [3.0, 4.0]
        d = calculate_cohen_d(group1, group2)
        assert d < 0

class TestSummaryStatisticsGeneration:
    @pytest.fixture
    def sample_beta_data(self):
        return [
            {'roi': 'VS', 'event_type': 'anticipation', 'group': 'excluded', 'beta_value': 0.5},
            {'roi': 'VS', 'event_type': 'anticipation', 'group': 'excluded', 'beta_value': 0.6},
            {'roi': 'VS', 'event_type': 'anticipation', 'group': 'excluded', 'beta_value': 0.4},
            {'roi': 'VS', 'event_type': 'anticipation', 'group': 'included', 'beta_value': 0.8},
            {'roi': 'VS', 'event_type': 'anticipation', 'group': 'included', 'beta_value': 0.9},
            {'roi': 'VS', 'event_type': 'anticipation', 'group': 'included', 'beta_value': 0.7},
            {'roi': 'OFC', 'event_type': 'receipt', 'group': 'excluded', 'beta_value': 1.0},
            {'roi': 'OFC', 'event_type': 'receipt', 'group': 'included', 'beta_value': 1.2},
        ]

    def test_generate_summary_statistics(self, sample_beta_data):
        results = generate_summary_statistics(sample_beta_data, alpha=0.05)
        
        assert len(results) == 2  # VS/anticipation and OFC/receipt
        
        # Check that all required fields are present
        for result in results:
            assert 'roi' in result
            assert 'event' in result
            assert 'n_excluded' in result
            assert 'n_included' in result
            assert 'mean_excluded' in result
            assert 'std_excluded' in result
            assert 'mean_included' in result
            assert 'std_included' in result
            assert 't_statistic' in result
            assert 'p_value_raw' in result
            assert 'p_value_bonferroni' in result
            assert 'cohens_d' in result

    def test_bonferroni_correction_applied(self, sample_beta_data):
        results = generate_summary_statistics(sample_beta_data, alpha=0.05)
        
        # With 2 tests, Bonferroni corrected alpha = 0.025
        # Raw p-values should be multiplied by 2 (or capped at 1)
        for result in results:
            assert result['p_value_bonferroni'] <= 1.0
            assert result['p_value_bonferroni'] >= result['p_value_raw']

    def test_missing_group_handling(self):
        data = [
            {'roi': 'VS', 'event_type': 'anticipation', 'group': 'excluded', 'beta_value': 0.5},
            # Missing 'included' group
        ]
        results = generate_summary_statistics(data, alpha=0.05)
        assert len(results) == 0  # Should skip incomplete groups

class TestSaveSummaryStatistics:
    def test_save_to_csv_and_json(self):
        results = [
            {
                'roi': 'VS',
                'event': 'anticipation',
                'n_excluded': 3,
                'n_included': 3,
                'mean_excluded': 0.5,
                'std_excluded': 0.1,
                'mean_included': 0.8,
                'std_included': 0.1,
                't_statistic': -2.5,
                'p_value_raw': 0.02,
                'p_value_bonferroni': 0.04,
                'cohens_d': -1.5
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_stats.json')
            save_summary_statistics(results, output_path)

            # Check CSV exists
            csv_path = output_path.replace('.json', '.csv')
            assert os.path.exists(csv_path)
            assert os.path.exists(output_path)

            # Verify CSV content
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                assert rows[0]['roi'] == 'VS'

            # Verify JSON content
            with open(output_path, 'r') as f:
                data = json.load(f)
                assert len(data) == 1
                assert data[0]['roi'] == 'VS'

class TestRunSummaryStatistics:
    def test_run_with_real_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create input file
            input_path = os.path.join(tmpdir, 'betas.csv')
            with open(input_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['participant_id', 'group', 'roi', 'event_type', 'beta_value'])
                writer.writerow(['sub-01', 'excluded', 'VS', 'anticipation', 0.5])
                writer.writerow(['sub-02', 'excluded', 'VS', 'anticipation', 0.6])
                writer.writerow(['sub-03', 'included', 'VS', 'anticipation', 0.8])
                writer.writerow(['sub-04', 'included', 'VS', 'anticipation', 0.9])

            output_path = os.path.join(tmpdir, 'stats.json')
            results = run_summary_statistics(input_path, output_path, alpha=0.05)

            assert len(results) == 1
            assert results[0]['roi'] == 'VS'
            assert results[0]['event'] == 'anticipation'

            # Check output files exist
            assert os.path.exists(output_path)
            assert os.path.exists(output_path.replace('.json', '.csv'))

    def test_run_with_missing_input(self):
        with pytest.raises(FileNotFoundError):
            run_summary_statistics("nonexistent.csv", "output.json")
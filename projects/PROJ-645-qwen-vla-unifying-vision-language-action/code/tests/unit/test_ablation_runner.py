"""
Unit tests for ablation_runner.py logic.

Tests the aggregation and CSV generation logic without running full training.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import csv
from unittest.mock import patch, MagicMock

# Add project root to path
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.experiments.ablation_runner import aggregate_results, run_ablation_study
from src.statistics.confidence_intervals import compute_confidence_intervals

class TestAblationRunnerLogic:
    """Test the aggregation logic of the ablation runner."""

    def test_aggregate_results_empty(self, tmp_path):
        """Test aggregation with no results."""
        results = {}
        output_path = tmp_path / "summary.csv"
        
        aggregate_results(results, output_path)
        
        # File should be created but empty (or header only)
        assert output_path.exists()
        with open(output_path, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            # Should have header
            assert len(rows) >= 1
            assert rows[0] == ['ratio', 'mean_success_rate', 'ci_lower', 'ci_upper', 'n_seeds']

    def test_aggregate_results_single_ratio(self, tmp_path):
        """Test aggregation with one ratio and multiple seeds."""
        # Mock results for ratio 0.5
        results = {
            0.5: [
                {'success_rate': 0.8},
                {'success_rate': 0.9},
                {'success_rate': 0.85}
            ]
        }
        output_path = tmp_path / "summary.csv"
        
        aggregate_results(results, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            row = rows[0]
            assert float(row['ratio']) == 0.5
            assert float(row['n_seeds']) == 3
            # Check that mean is roughly correct (0.85)
            assert 0.8 < float(row['mean_success_rate']) < 0.9
            # Check CI bounds are reasonable
            assert float(row['ci_lower']) < float(row['mean_success_rate'])
            assert float(row['ci_upper']) > float(row['mean_success_rate'])

    def test_aggregate_results_multiple_ratios(self, tmp_path):
        """Test aggregation with multiple ratios."""
        results = {
            0.0: [{'success_rate': 0.5}, {'success_rate': 0.6}],
            1.0: [{'success_rate': 0.9}, {'success_rate': 0.95}]
        }
        output_path = tmp_path / "summary.csv"
        
        aggregate_results(results, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            
            # Check ratios are present
            ratios = {float(r['ratio']) for r in rows}
            assert 0.0 in ratios
            assert 1.0 in ratios
            
            # Check that 1.0 has higher mean than 0.0
            row_1 = next(r for r in rows if float(r['ratio']) == 1.0)
            row_0 = next(r for r in rows if float(r['ratio']) == 0.0)
            assert float(row_1['mean_success_rate']) > float(row_0['mean_success_rate'])

    def test_aggregate_results_with_list_rates(self, tmp_path):
        """Test aggregation when success_rate is a list (e.g., per-task)."""
        results = {
            0.5: [
                {'success_rate': [0.8, 0.9]}, # Mean 0.85
                {'success_rate': [0.7, 0.8]}  # Mean 0.75
            ]
        }
        output_path = tmp_path / "summary.csv"
        
        aggregate_results(results, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            # Expected mean of means: (0.85 + 0.75) / 2 = 0.8
            assert abs(float(rows[0]['mean_success_rate']) - 0.8) < 0.01

    def test_aggregate_results_missing_keys(self, tmp_path):
        """Test aggregation when some results are missing success_rate."""
        results = {
            0.5: [
                {'success_rate': 0.8},
                {'other_metric': 0.9}, # Should be skipped or handled
                {'mean_success_rate': 0.85}
            ]
        }
        output_path = tmp_path / "summary.csv"
        
        aggregate_results(results, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            # Should have processed at least the valid ones
            assert len(rows) == 1

class TestAblationStudyIntegration:
    """Integration tests for the ablation study runner (mocked)."""

    @patch('src.experiments.ablation_runner.run_single_ablation_run')
    @patch('src.experiments.ablation_runner.load_seeds')
    def test_run_ablation_study_mocked(self, mock_load_seeds, mock_run_single, tmp_path):
        """Test the main study runner with mocked training/eval."""
        mock_load_seeds.return_value = [1, 2]
        mock_run_single.side_effect = [
            {'success_rate': 0.8}, # ratio 0.0, seed 1
            {'success_rate': 0.85}, # ratio 0.0, seed 2
            {'success_rate': 0.9},  # ratio 1.0, seed 1
            {'success_rate': 0.95}  # ratio 1.0, seed 2
        ]
        
        from src.utils.config import Config
        config = Config()
        
        csv_path = run_ablation_study(
            ratios=[0.0, 1.0],
            output_dir=tmp_path,
            config=config
        )
        
        assert csv_path.exists()
        mock_load_seeds.assert_called()
        assert mock_run_single.call_count == 4 # 2 ratios * 2 seeds
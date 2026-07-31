"""
Unit tests for generate_baseline_comparison.py (Task T022).
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from generate_baseline_comparison import (
    load_simulation_data,
    calculate_tokens,
    calculate_win,
    aggregate_metrics,
    generate_baseline_comparison
)

class TestCalculateTokens:
    def test_total_tokens_field(self):
        row = {"total_tokens": 100}
        assert calculate_tokens(row) == 100

    def test_tokens_used_field(self):
        row = {"tokens_used": 250}
        assert calculate_tokens(row) == 250

    def test_fallback_token_field(self):
        row = {"prompt_tokens": 500, "completion_tokens": 200}
        assert calculate_tokens(row) == 500  # First match

    def test_missing_token_field(self):
        row = {"some_other_field": 123}
        assert calculate_tokens(row) == 0

class TestCalculateWin:
    def test_win_true(self):
        row = {"win": True}
        assert calculate_win(row) is True

    def test_win_false(self):
        row = {"win": False}
        assert calculate_win(row) is False

    def test_success_field(self):
        row = {"success": True}
        assert calculate_win(row) is True

    def test_outcome_win(self):
        row = {"outcome": "win"}
        assert calculate_win(row) is True

    def test_missing_win_field(self):
        row = {"some_field": 123}
        assert calculate_win(row) is False

class TestAggregateMetrics:
    def test_empty_results(self):
        result = aggregate_metrics([], "test")
        assert result['condition'] == "test"
        assert result['win_rate'] == 0.0
        assert result['avg_tokens'] == 0.0
        assert result['std_dev_tokens'] == 0.0

    def test_single_result(self):
        results = [{"total_tokens": 100, "win": True}]
        result = aggregate_metrics(results, "test")
        assert result['avg_tokens'] == 100.0
        assert result['std_dev_tokens'] == 0.0
        assert result['win_rate'] == 1.0

    def test_multiple_results(self):
        results = [
            {"total_tokens": 100, "win": True},
            {"total_tokens": 200, "win": False},
            {"total_tokens": 300, "win": True}
        ]
        result = aggregate_metrics(results, "test")
        assert result['avg_tokens'] == 200.0
        assert result['win_rate'] == 2/3
        # Std dev calculation: variance = ((100-200)^2 + (200-200)^2 + (300-200)^2) / 2 = (10000 + 0 + 10000) / 2 = 10000
        # std_dev = 100.0
        assert abs(result['std_dev_tokens'] - 100.0) < 0.01

class TestLoadSimulationData:
    def test_load_list_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.json"
            data = [{"id": 1}, {"id": 2}]
            with open(test_file, 'w') as f:
                json.dump(data, f)
            
            result = load_simulation_data(test_file)
            assert len(result) == 2
            assert result[0]['id'] == 1

    def test_load_dict_with_results(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.json"
            data = {"results": [{"id": 1}, {"id": 2}]}
            with open(test_file, 'w') as f:
                json.dump(data, f)
            
            result = load_simulation_data(test_file)
            assert len(result) == 2

    def test_missing_file(self):
        result = load_simulation_data(Path("/nonexistent/file.json"))
        assert result is None

    def test_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.json"
            with open(test_file, 'w') as f:
                f.write("invalid json {")
            
            result = load_simulation_data(test_file)
            assert result is None

class TestGenerateBaselineComparison:
    def test_full_flow_with_mock_data(self, tmp_path):
        # Setup temporary directories
        data_processed = tmp_path / "data" / "processed"
        data_processed.mkdir(parents=True)

        # Create mock simulation logs
        dynamic_data = [
            {"trajectory_id": "1", "total_tokens": 1000, "win": True},
            {"trajectory_id": "2", "total_tokens": 1200, "win": False},
            {"trajectory_id": "3", "total_tokens": 1100, "win": True}
        ]
        static_data = [
            {"trajectory_id": "1", "total_tokens": 2000, "win": True},
            {"trajectory_id": "2", "total_tokens": 2200, "win": True},
            {"trajectory_id": "3", "total_tokens": 2100, "win": False}
        ]
        random_data = [
            {"trajectory_id": "1", "total_tokens": 1800, "win": False},
            {"trajectory_id": "2", "total_tokens": 1900, "win": True},
            {"trajectory_id": "3", "total_tokens": 1850, "win": False}
        ]

        # Write mock files
        dynamic_file = data_processed / "simulation_logs_dynamic.json"
        static_file = data_processed / "simulation_logs_static.json"
        random_file = data_processed / "simulation_logs_random.json"

        with open(dynamic_file, 'w') as f:
            json.dump(dynamic_data, f)
        with open(static_file, 'w') as f:
            json.dump(static_data, f)
        with open(random_file, 'w') as f:
            json.dump(random_data, f)

        # Temporarily override paths in the module
        import generate_baseline_comparison as gbc
        original_dynamic = gbc.DYNAMIC_LOG
        original_static = gbc.STATIC_LOG
        original_random = gbc.RANDOM_LOG
        original_output = gbc.OUTPUT_CSV
        original_status = gbc.BUILD_STATUS_FILE
        original_data_processed = gbc.DATA_PROCESSED

        gbc.DYNAMIC_LOG = dynamic_file
        gbc.STATIC_LOG = static_file
        gbc.RANDOM_LOG = random_file
        gbc.OUTPUT_CSV = data_processed / "baseline_comparison.csv"
        gbc.BUILD_STATUS_FILE = data_processed / "build_status.json"
        gbc.DATA_PROCESSED = data_processed

        try:
            success = generate_baseline_comparison()
            assert success is True

            # Check CSV output
            csv_path = data_processed / "baseline_comparison.csv"
            assert csv_path.exists()
            df = pd.read_csv(csv_path)
            
            assert len(df) == 3
            assert set(df['condition']) == {'dynamic', 'static', 'random'}
            
            # Check that token reduction was calculated
            dynamic_row = df[df['condition'] == 'dynamic'].iloc[0]
            # (2100 - 1100) / 2100 = 1000/2100 ≈ 0.476
            expected_reduction = (2100 - 1100) / 2100
            assert abs(dynamic_row['token_reduction_pct'] - expected_reduction) < 0.01
            assert dynamic_row['threshold_met'] is True  # > 30%

            # Check build status
            status_file = data_processed / "build_status.json"
            assert status_file.exists()
            with open(status_file, 'r') as f:
                status = json.load(f)
            assert status['threshold_met'] is True
        finally:
            # Restore original paths
            gbc.DYNAMIC_LOG = original_dynamic
            gbc.STATIC_LOG = original_static
            gbc.RANDOM_LOG = original_random
            gbc.OUTPUT_CSV = original_output
            gbc.BUILD_STATUS_FILE = original_status
            gbc.DATA_PROCESSED = original_data_processed

    def test_missing_static_data(self, tmp_path):
        # Setup
        data_processed = tmp_path / "data" / "processed"
        data_processed.mkdir(parents=True)

        # Only create dynamic file, not static
        dynamic_data = [{"total_tokens": 100, "win": True}]
        dynamic_file = data_processed / "simulation_logs_dynamic.json"
        with open(dynamic_file, 'w') as f:
            json.dump(dynamic_data, f)

        import generate_baseline_comparison as gbc
        original_dynamic = gbc.DYNAMIC_LOG
        original_static = gbc.STATIC_LOG
        original_random = gbc.RANDOM_LOG
        original_data_processed = gbc.DATA_PROCESSED

        gbc.DYNAMIC_LOG = dynamic_file
        gbc.STATIC_LOG = data_processed / "simulation_logs_static.json"  # Missing
        gbc.RANDOM_LOG = data_processed / "simulation_logs_random.json"  # Missing
        gbc.DATA_PROCESSED = data_processed

        try:
            success = generate_baseline_comparison()
            assert success is False
        finally:
            gbc.DYNAMIC_LOG = original_dynamic
            gbc.STATIC_LOG = original_static
            gbc.RANDOM_LOG = original_random
            gbc.DATA_PROCESSED = original_data_processed
import os
import sys
import tempfile
import csv
from pathlib import Path
import pytest

# Add project root to path if running from tests directory
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.evaluation.metrics import (
    calculate_rmse,
    calculate_mae,
    load_forecasts,
    load_outcomes,
    evaluate_frequentist_methods
)

class TestRMSE:
    def test_rmse_perfect_prediction(self):
        actuals = [50.0, 51.0, 49.5]
        predictions = [50.0, 51.0, 49.5]
        assert calculate_rmse(actuals, predictions) == 0.0

    def test_rmse_constant_error(self):
        actuals = [50.0, 50.0, 50.0]
        predictions = [52.0, 52.0, 52.0]
        # Error is 2.0 for all, so RMSE should be 2.0
        assert calculate_rmse(actuals, predictions) == 2.0

    def test_rmse_mixed_errors(self):
        actuals = [0.0, 10.0]
        predictions = [1.0, 9.0]
        # Errors: 1, 1 -> MSE = 1 -> RMSE = 1
        assert calculate_rmse(actuals, predictions) == 1.0

    def test_rmse_empty_list(self):
        with pytest.raises(ValueError):
            calculate_rmse([], [])

    def test_rmse_mismatched_lengths(self):
        with pytest.raises(ValueError):
            calculate_rmse([1.0, 2.0], [1.0])

class TestMAE:
    def test_mae_perfect_prediction(self):
        actuals = [50.0, 51.0, 49.5]
        predictions = [50.0, 51.0, 49.5]
        assert calculate_mae(actuals, predictions) == 0.0

    def test_mae_constant_error(self):
        actuals = [50.0, 50.0, 50.0]
        predictions = [52.0, 52.0, 52.0]
        assert calculate_mae(actuals, predictions) == 2.0

    def test_mae_mixed_errors(self):
        actuals = [0.0, 10.0]
        predictions = [1.0, 9.0]
        # Errors: 1, 1 -> MAE = 1
        assert calculate_mae(actuals, predictions) == 1.0

    def test_mae_empty_list(self):
        with pytest.raises(ValueError):
            calculate_mae([], [])

    def test_mae_mismatched_lengths(self):
        with pytest.raises(ValueError):
            calculate_mae([1.0, 2.0], [1.0])

class TestEvaluateFrequentistMethods:
    @pytest.fixture
    def temp_forecast_file(self, tmp_path):
        data = [
            {"election_date": "2020-11-03", "candidate": "A", "simple_avg_forecast": 49.0, "weighted_avg_forecast": 50.0},
            {"election_date": "2020-11-03", "candidate": "B", "simple_avg_forecast": 51.0, "weighted_avg_forecast": 50.0},
            {"election_date": "2016-11-08", "candidate": "A", "simple_avg_forecast": 45.0, "weighted_avg_forecast": 46.0},
        ]
        filepath = tmp_path / "frequentist_forecasts.csv"
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        return str(filepath)

    @pytest.fixture
    def temp_outcome_file(self, tmp_path):
        data = [
            {"election_date": "2020-11-03", "candidate": "A", "actual_vote_share": 51.0},
            {"election_date": "2020-11-03", "candidate": "B", "actual_vote_share": 49.0},
            {"election_date": "2016-11-08", "candidate": "A", "actual_vote_share": 48.0},
        ]
        filepath = tmp_path / "election_outcomes.csv"
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        return str(filepath)

    def test_evaluate_methods(self, temp_forecast_file, temp_outcome_file, tmp_path):
        output_path = str(tmp_path / "metrics.csv")
        
        metrics = evaluate_frequentist_methods(
            temp_forecast_file,
            temp_outcome_file,
            output_path
        )
        
        # Check 2020-11-03, A: Simple (49 vs 51 -> err 2), Weighted (50 vs 51 -> err 1)
        # Check 2020-11-03, B: Simple (51 vs 49 -> err 2), Weighted (50 vs 49 -> err 1)
        # Check 2016-11-08, A: Simple (45 vs 48 -> err 3), Weighted (46 vs 48 -> err 2)
        
        # Simple Errors: 2, 2, 3 -> MSE = (4+4+9)/3 = 17/3 = 5.666... -> RMSE = sqrt(5.666)
        # Weighted Errors: 1, 1, 2 -> MSE = (1+1+4)/3 = 6/3 = 2 -> RMSE = sqrt(2)
        
        import math
        expected_simple_rmse = math.sqrt(17/3)
        expected_weighted_rmse = math.sqrt(2)
        
        assert abs(metrics['simple_average']['rmse'] - expected_simple_rmse) < 1e-6
        assert abs(metrics['weighted_average']['rmse'] - expected_weighted_rmse) < 1e-6
        
        # Check file was written
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]['method'] == 'simple_average'
            assert rows[1]['method'] == 'weighted_average'

    def test_no_matching_data(self, tmp_path):
        # Create forecast file with no matching keys
        forecast_data = [{"election_date": "2020-01-01", "candidate": "X", "simple_avg_forecast": 50.0, "weighted_avg_forecast": 50.0}]
        forecast_file = tmp_path / "forecasts.csv"
        with open(forecast_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=forecast_data[0].keys())
            writer.writeheader()
            writer.writerows(forecast_data)
        
        outcome_data = [{"election_date": "2021-01-01", "candidate": "Y", "actual_vote_share": 50.0}]
        outcome_file = tmp_path / "outcomes.csv"
        with open(outcome_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=outcome_data[0].keys())
            writer.writeheader()
            writer.writerows(outcome_data)
        
        output_file = tmp_path / "metrics.csv"
        
        with pytest.raises(ValueError, match="No matching data found"):
            evaluate_frequentist_methods(str(forecast_file), str(outcome_file), str(output_file))
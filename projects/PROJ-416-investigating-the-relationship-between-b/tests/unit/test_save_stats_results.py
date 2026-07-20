import csv
import os
import tempfile
from pathlib import Path
import pytest

from code.analysis.save_stats_results import load_stats_results_from_dict, save_stats_to_csv, run_save_stats_results
from code.config import Config

class TestLoadStatsResults:
    def test_load_from_flat_dict(self):
        data = {
            "results": [
                {"metric_name": "GlobalEfficiency", "coef": 0.5, "p_value": 0.01, "vif": 1.2},
                {"metric_name": "Modularity", "coef": 0.3, "p_value": 0.04, "vif": 1.1}
            ]
        }
        rows = load_stats_results_from_dict(data)
        assert len(rows) == 2
        assert rows[0]["metric_name"] == "GlobalEfficiency"

    def test_load_from_nested_dict(self):
        data = {
            "results": {
                "GlobalEfficiency": {"coef": 0.5, "p_value": 0.01},
                "Modularity": {"coef": 0.3, "p_value": 0.04}
            }
        }
        rows = load_stats_results_from_dict(data)
        assert len(rows) == 2
        assert rows[0]["metric_name"] == "GlobalEfficiency"

    def test_load_empty(self):
        assert load_stats_results_from_dict({}) == []
        assert load_stats_results_from_dict(None) == []

class TestSaveStatsToCsv:
    def test_save_valid_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_stats.csv"
            data = [
                {"metric_name": "GlobalEfficiency", "coef": 0.5, "p_value": 0.01, "vif": 1.2, "fdr_corrected": True, "power": 0.8, "min_n": 10, "model_type": "ancova"},
                {"metric_name": "Modularity", "coef": 0.3, "p_value": 0.04, "vif": 1.1, "fdr_corrected": False, "power": 0.6, "min_n": 15, "model_type": "univariate"}
            ]
            save_stats_to_csv(data, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]["metric_name"] == "GlobalEfficiency"
                assert rows[0]["coef"] == "0.500000"
                assert rows[0]["p_value"] == "0.010000"

    def test_save_empty_data_creates_headers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_empty.csv"
            save_stats_to_csv([], output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 0
                # Check headers exist
                assert "metric_name" in reader.fieldnames

class TestRunSaveStatsResults:
    def test_integration(self):
        config = Config()
        # Ensure paths exist
        config.PATHS.METRICS_DIR.mkdir(parents=True, exist_ok=True)
        
        stats_data = {
            "results": [
                {"metric_name": "TestMetric", "coef": 0.99, "p_value": 0.001, "vif": 1.0, "fdr_corrected": True, "power": 0.95, "min_n": 5, "model_type": "ancova"}
            ]
        }
        
        output_path = run_save_stats_results(config, stats_data)
        
        assert output_path.exists()
        assert output_path.name == "statistical_results.csv"
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["coef"] == "0.990000"
            assert rows[0]["min_n"] == "5"
            assert rows[0]["model_type"] == "ancova"
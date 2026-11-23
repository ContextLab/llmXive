import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
import pytest

# Add the code directory to the path if running from tests
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.evaluation.stats import (
    load_evaluation_results,
    extract_success_rates,
    perform_paired_test,
    apply_benjamini_hochberg,
    compare_strategies,
    save_statistics_report
)

class TestLoadEvaluationResults:
    def test_load_valid_json(self, tmp_path):
        data = {"strategy_a": [1, 1, 0], "strategy_b": [1, 0, 0]}
        file_path = tmp_path / "results.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        result = load_evaluation_results(file_path)
        assert result == data

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_evaluation_results(tmp_path / "nonexistent.json")

class TestExtractSuccessRates:
    def test_calculate_rates(self):
        data = {"A": [1, 1, 1], "B": [1, 0, 0]}
        rates = extract_success_rates(data)
        assert rates["A"] == 1.0
        assert rates["B"] == pytest.approx(0.333, rel=0.01)
    
    def test_empty_list(self):
        data = {"A": []}
        rates = extract_success_rates(data)
        assert rates["A"] == 0.0

class TestPerformPairedTest:
    def test_paired_data(self):
        a = [1, 1, 0, 1]
        b = [1, 0, 0, 1]
        stat, p_val = perform_paired_test(a, b)
        assert isinstance(stat, float)
        assert isinstance(p_val, float)
        assert 0 <= p_val <= 1

    def test_unpaired_data_fallback(self):
        a = [1, 1, 0]
        b = [1, 0, 0, 1] # Different length
        stat, p_val = perform_paired_test(a, b)
        assert isinstance(stat, float)
        assert isinstance(p_val, float)

class TestBenjaminiHochberg:
    def test_simple_correction(self):
        p_values = [0.01, 0.04, 0.03, 0.005]
        corrected = apply_benjamini_hochberg(p_values)
        assert len(corrected) == 4
        assert all(0 <= p <= 1 for p in corrected)
        # Corrected values should generally be >= original (or 1.0)
        # But due to monotonicity, they might be larger.
        # We just check validity.
    
    def test_empty_list(self):
        assert apply_benjamini_hochberg([]) == []

class TestCompareStrategies:
    def test_compare_with_baseline(self, tmp_path):
        # Mock the results
        results = {
            "baseline": [1, 1, 1, 1, 1],
            "strategy_a": [1, 1, 1, 1, 1],
            "strategy_b": [0, 0, 0, 0, 0]
        }
        
        comparisons = compare_strategies(results, "baseline")
        
        assert "strategy_a" in comparisons
        assert "strategy_b" in comparisons
        assert "baseline" not in comparisons
        assert 0 <= comparisons["strategy_a"]["p_value"] <= 1
        assert 0 <= comparisons["strategy_b"]["p_value"] <= 1

    def test_missing_baseline(self):
        results = {"strategy_a": [1, 0]}
        with pytest.raises(ValueError, match="Baseline strategy"):
            compare_strategies(results, "nonexistent_baseline")

class TestSaveStatisticsReport:
    def test_save_report(self, tmp_path):
        report = {"test": "value", "p_values": [0.05, 0.01]}
        output_path = tmp_path / "stats.json"
        save_statistics_report(report, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        assert loaded == report
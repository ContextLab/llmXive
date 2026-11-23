import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.evaluation.stats import (
    load_evaluation_results,
    extract_success_rates,
    perform_paired_test,
    apply_benjamini_hochberg,
    calculate_statistical_power,
    compare_strategies,
    save_statistics_report,
    main
)

class TestLoadEvaluationResults:
    def test_load_existing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / "test.json"
            test_data = {"key": "value"}
            with open(test_path, 'w') as f:
                json.dump(test_data, f)
            
            result = load_evaluation_results(test_path)
            assert result == test_data

    def test_load_nonexistent_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / "nonexistent.json"
            with pytest.raises(FileNotFoundError):
                load_evaluation_results(test_path)

class TestExtractSuccessRates:
    def test_extract_rates(self):
        report = {
            "strategy_results": {
                "baseline": {"mean_success_rate": 0.8, "success_rates": [0.8, 0.9]},
                "strategy_a": {"mean_success_rate": 0.7, "success_rates": [0.7, 0.6]}
            }
        }
        rates = extract_success_rates(report)
        assert "baseline" in rates
        assert "strategy_a" in rates
        assert rates["baseline"] == 0.8

    def test_missing_key(self):
        report = {"other_key": {}}
        with pytest.raises(ValueError):
            extract_success_rates(report)

class TestPerformPairedTest:
    def test_ttest(self):
        # Data that should pass normality check
        group1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        group2 = [1.1, 2.1, 3.1, 4.1, 5.1]
        stat, p_val = perform_paired_test(group1, group2)
        assert isinstance(stat, float)
        assert 0.0 <= p_val <= 1.0

    def test_insufficient_data(self):
        with pytest.raises(ValueError):
            perform_paired_test([1.0], [1.0])

    def test_unequal_lengths(self):
        with pytest.raises(ValueError):
            perform_paired_test([1.0, 2.0], [1.0])

class TestBenjaminiHochberg:
    def test_basic_correction(self):
        p_values = [0.01, 0.04, 0.03, 0.20]
        adjusted = apply_benjamini_hochberg(p_values)
        assert len(adjusted) == len(p_values)
        assert all(0.0 <= p <= 1.0 for p in adjusted)

    def test_empty_list(self):
        assert apply_benjamini_hochberg([]) == []

class TestCalculateStatisticalPower:
    def test_high_power_with_large_n(self):
        power = calculate_statistical_power(n=100, effect_size=0.8)
        assert power > 0.8

    def test_low_power_with_small_n(self):
        power = calculate_statistical_power(n=5, effect_size=0.5)
        assert power < 0.8

    def test_zero_n(self):
        power = calculate_statistical_power(n=0, effect_size=0.5)
        assert power == 0.0

class TestCompareStrategies:
    def test_compare_two_strategies(self):
        results = {
            "baseline": {
                "success_rates": [0.8, 0.9, 0.85, 0.9, 0.88],
                "mean_success_rate": 0.866
            },
            "new_strategy": {
                "success_rates": [0.7, 0.75, 0.72, 0.78, 0.76],
                "mean_success_rate": 0.742
            }
        }
        comparisons = compare_strategies(results)
        assert len(comparisons) == 1
        assert comparisons[0][0] == "new_strategy"
        assert isinstance(comparisons[0][1], float)
        assert isinstance(comparisons[0][2], float)

    def test_missing_baseline(self):
        results = {"strategy_a": {"success_rates": [0.5]}}
        with pytest.raises(ValueError):
            compare_strategies(results, baseline_strategy="nonexistent")

class TestSaveStatisticsReport:
    def test_save_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.json"
            report = {"test": "data"}
            save_statistics_report(report, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            assert loaded == report

class TestMain:
    @patch('src.evaluation.stats.get_results_path')
    @patch('src.evaluation.stats.get_project_root')
    def test_main_with_valid_report(self, mock_root, mock_results):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_root.return_value = Path(tmpdir)
            mock_results.return_value = Path(tmpdir)
            
            report_path = Path(tmpdir) / "stats_report.json"
            test_report = {
                "strategy_results": {
                    "baseline": {
                        "success_rates": [0.8, 0.9, 0.85, 0.9, 0.88],
                        "mean_success_rate": 0.866
                    },
                    "strategy_a": {
                        "success_rates": [0.7, 0.75, 0.72, 0.78, 0.76],
                        "mean_success_rate": 0.742
                    }
                }
            }
            
            with open(report_path, 'w') as f:
                json.dump(test_report, f)
            
            # Run main
            main()
            
            # Verify report was updated with power analysis
            with open(report_path, 'r') as f:
                updated_report = json.load(f)
            
            assert "power_analysis" in updated_report
            assert "estimated_power" in updated_report["power_analysis"]
            assert "observed_effect_size" in updated_report["power_analysis"]
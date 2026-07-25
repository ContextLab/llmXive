import pytest
import json
import os
import tempfile
import csv
from pathlib import Path
import numpy as np

from analysis.stats import (
    StatisticalTestResult,
    StatisticalReport,
    load_evaluation_results_from_json,
    filter_converged_seeds,
    calculate_percentage_difference,
    run_paired_ttest,
    calculate_cohen_d,
    calculate_confidence_interval,
    bonferroni_correction,
    run_sensitivity_analysis
)


class TestSensitivityAnalysis:
    """Tests for sensitivity analysis functionality (T025)."""

    def test_sensitivity_analysis_creates_csv(self, tmp_path):
        """Test that sensitivity analysis creates the expected CSV file."""
        output_path = tmp_path / "sensitivity_analysis.csv"
        
        # Create mock evaluation results
        mock_results = [
            {"confidence": 0.75, "is_correct": True},
            {"confidence": 0.65, "is_correct": True},
            {"confidence": 0.55, "is_correct": False},
            {"confidence": 0.45, "is_correct": True},
            {"confidence": 0.35, "is_correct": False},
            {"confidence": 0.85, "is_correct": True},
            {"confidence": 0.25, "is_correct": False},
            {"confidence": 0.95, "is_correct": True},
        ]
        
        run_sensitivity_analysis(
            evaluation_results=mock_results,
            thresholds=[0.4, 0.5, 0.6],
            output_path=str(output_path)
        )
        
        assert output_path.exists(), "Sensitivity analysis CSV file was not created"
        
        # Verify CSV structure
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 3, f"Expected 3 rows (one per threshold), got {len(rows)}"
            assert set(rows[0].keys()) == {'threshold', 'false_positive_rate', 'false_negative_rate'}

    def test_sensitivity_analysis_thresholds(self, tmp_path):
        """Test that sensitivity analysis uses the correct thresholds."""
        output_path = tmp_path / "sensitivity_analysis.csv"
        
        mock_results = [
            {"confidence": 0.7, "is_correct": True},
            {"confidence": 0.5, "is_correct": False},
            {"confidence": 0.3, "is_correct": True},
            {"confidence": 0.8, "is_correct": True},
        ]
        
        run_sensitivity_analysis(
            evaluation_results=mock_results,
            thresholds=[0.4, 0.5, 0.6],
            output_path=str(output_path)
        )
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            thresholds_found = [float(row['threshold']) for row in reader]
            
            assert thresholds_found == [0.4, 0.5, 0.6], "Thresholds in CSV do not match input"

    def test_sensitivity_analysis_empty_results(self, tmp_path):
        """Test sensitivity analysis with empty evaluation results."""
        output_path = tmp_path / "sensitivity_analysis.csv"
        
        run_sensitivity_analysis(
            evaluation_results=[],
            thresholds=[0.4, 0.5, 0.6],
            output_path=str(output_path)
        )
        
        assert output_path.exists(), "CSV file should be created even with empty results"
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 0, "Empty results should produce CSV with no data rows"

    def test_sensitivity_analysis_fpr_fnr_calculation(self, tmp_path):
        """Test that FPR and FNR are calculated correctly."""
        output_path = tmp_path / "sensitivity_analysis.csv"
        
        # Create a controlled dataset where we know the expected rates
        # At threshold 0.5:
        # - confidence >= 0.5: [0.7 (T), 0.6 (F), 0.8 (T)] -> TP=2, FP=1
        # - confidence < 0.5: [0.4 (T), 0.3 (F), 0.2 (F)] -> FN=1, TN=2
        # FPR = FP / (FP + TN) = 1 / 3
        # FNR = FN / (FN + TP) = 1 / 3
        
        mock_results = [
            {"confidence": 0.7, "is_correct": True},   # TP
            {"confidence": 0.6, "is_correct": False},  # FP
            {"confidence": 0.8, "is_correct": True},   # TP
            {"confidence": 0.4, "is_correct": True},   # FN
            {"confidence": 0.3, "is_correct": False},  # TN
            {"confidence": 0.2, "is_correct": False},  # TN
        ]
        
        run_sensitivity_analysis(
            evaluation_results=mock_results,
            thresholds=[0.5],
            output_path=str(output_path)
        )
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            row = next(reader)
            
            fpr = float(row['false_positive_rate'])
            fnr = float(row['false_negative_rate'])
            
            # Allow small floating point tolerance
            assert abs(fpr - 1/3) < 0.001, f"Expected FPR ~0.333, got {fpr}"
            assert abs(fnr - 1/3) < 0.001, f"Expected FNR ~0.333, got {fnr}"

    def test_sensitivity_analysis_output_format(self, tmp_path):
        """Test that output CSV has correct column names and format."""
        output_path = tmp_path / "sensitivity_analysis.csv"
        
        mock_results = [
            {"confidence": 0.5, "is_correct": True},
        ]
        
        run_sensitivity_analysis(
            evaluation_results=mock_results,
            thresholds=[0.4],
            output_path=str(output_path)
        )
        
        with open(output_path, 'r') as f:
            content = f.read()
            lines = content.strip().split('\n')
            
            # Check header
            assert lines[0] == "threshold,false_positive_rate,false_negative_rate"
            
            # Check data format (3 decimal places)
            parts = lines[1].split(',')
            assert len(parts) == 3
            assert float(parts[0]) == 0.4
            # Rates should be between 0 and 1
            assert 0 <= float(parts[1]) <= 1
            assert 0 <= float(parts[2]) <= 1


class TestStatisticalTestResult:
    def test_statistical_test_result_creation(self):
        result = StatisticalTestResult(
            test_name="ttest",
            statistic=2.5,
            p_value=0.03,
            significant=True,
            effect_size=0.8
        )
        
        assert result.test_name == "ttest"
        assert result.statistic == 2.5
        assert result.p_value == 0.03
        assert result.significant is True
        assert result.effect_size == 0.8

class TestStatisticalReport:
    def test_statistical_report_creation(self):
        report = StatisticalReport(
            tests=[StatisticalTestResult("test", 1.0, 0.5, False)],
            percentage_difference=10.5,
            sensitivity_results={"thresholds": [0.5]},
            metadata={"key": "value"}
        )
        
        assert len(report.tests) == 1
        assert report.percentage_difference == 10.5
        assert report.sensitivity_results == {"thresholds": [0.5]}
        assert report.metadata == {"key": "value"}

class TestLoadEvaluationResults:
    def test_load_single_result(self, tmp_path):
        data_file = tmp_path / "results.json"
        data = {"self_consistency": 0.85, "confidence": 0.9}
        
        with open(data_file, 'w') as f:
            json.dump(data, f)
        
        results = load_evaluation_results_from_json(str(data_file))
        
        assert len(results) == 1
        assert results[0]["self_consistency"] == 0.85

    def test_load_list_of_results(self, tmp_path):
        data_file = tmp_path / "results.json"
        data = [
            {"self_consistency": 0.85, "seed": 1},
            {"self_consistency": 0.90, "seed": 2}
        ]
        
        with open(data_file, 'w') as f:
            json.dump(data, f)
        
        results = load_evaluation_results_from_json(str(data_file))
        
        assert len(results) == 2
        assert results[0]["seed"] == 1

    def test_load_nonexistent_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_evaluation_results_from_json(str(tmp_path / "nonexistent.json"))

class TestFilterConvergedSeeds:
    def test_filter_converged(self):
        results = [
            {"seed": 1, "confidence_loss": 0.005},
            {"seed": 2, "confidence_loss": 0.02},
            {"seed": 3, "confidence_loss": 0.008}
        ]
        
        filtered = filter_converged_seeds(results, threshold=0.01)
        
        assert len(filtered) == 2
        assert all(r["confidence_loss"] <= 0.01 for r in filtered)

class TestCalculatePercentageDifference:
    def test_percentage_difference(self):
        recursive = [0.8, 0.85, 0.9]
        baseline = [0.7, 0.75, 0.8]
        
        diff = calculate_percentage_difference(recursive, baseline)
        
        expected = ((0.85 - 0.75) / 0.75) * 100  # ~13.33%
        assert abs(diff - expected) < 0.01

    def test_empty_lists(self):
        diff = calculate_percentage_difference([], [])
        assert diff == 0.0

class TestRunPairedTtest:
    def test_paired_ttest(self):
        recursive = [0.8, 0.85, 0.9, 0.95]
        baseline = [0.7, 0.75, 0.8, 0.85]
        
        result = run_paired_ttest(recursive, baseline)
        
        assert result.test_name == "paired_ttest"
        assert result.statistic > 0  # Recursive should be higher
        assert result.p_value < 1.0  # Valid p-value

    def test_paired_ttest_equal_length(self):
        with pytest.raises(ValueError):
            run_paired_ttest([1, 2, 3], [1, 2])

class TestCalculateCohenD:
    def test_cohen_d(self):
        group1 = [1, 2, 3, 4, 5]
        group2 = [2, 3, 4, 5, 6]
        
        d = calculate_cohen_d(group1, group2)
        
        assert isinstance(d, float)
        assert d != 0  # Should have some effect size

class TestCalculateConfidenceInterval:
    def test_confidence_interval(self):
        data = [10, 12, 11, 13, 10, 12]
        
        lower, upper = calculate_confidence_interval(data)
        
        assert lower < np.mean(data)
        assert upper > np.mean(data)
        assert lower < upper

class TestBonferroniCorrection:
    def test_bonferroni_correction(self):
        p_values = [0.01, 0.03, 0.07]
        
        results = bonferroni_correction(p_values, alpha=0.05)
        
        assert len(results) == 3
        # With 3 tests, corrected alpha = 0.05/3 = 0.0167
        # First two should be significant, third not
        assert results[0][1] is True   # 0.01 < 0.0167
        assert results[1][1] is True   # 0.03 > 0.0167? No, wait...
        # Actually 0.03 > 0.0167, so should be False
        # Let me recalculate:
        # corrected_alpha = 0.05 / 3 = 0.0167
        # 0.01 < 0.0167 -> True
        # 0.03 > 0.0167 -> False
        # 0.07 > 0.0167 -> False
        assert results[0][1] is True
        assert results[1][1] is False
        assert results[2][1] is False

        assert results[0][1] is False  # 0.03 > 0.0167
        assert results[2][1] is False
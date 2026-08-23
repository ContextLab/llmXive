import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

from src.stats.significance import (
    check_sample_sizes,
    has_low_sample_count,
    perform_anova,
    bonferroni_correction,
    analyze_significance,
    run_pipeline
)


class TestSampleSizeChecks:
    def test_check_sample_sizes_all_pass(self):
        scores = {
            "color": [0.1] * 50,
            "pattern": [0.2] * 50,
            "texture": [0.3] * 50
        }
        result = check_sample_sizes(scores, min_n=30)
        assert all(result.values())
        assert len(result) == 3

    def test_check_sample_sizes_some_fail(self):
        scores = {
            "color": [0.1] * 50,
            "pattern": [0.2] * 10,
            "texture": [0.3] * 25
        }
        result = check_sample_sizes(scores, min_n=30)
        assert result["color"] is True
        assert result["pattern"] is False
        assert result["texture"] is False

    def test_has_low_sample_count(self):
        scores = {
            "color": [0.1] * 50,
            "pattern": [0.2] * 10,
            "texture": [0.3] * 25
        }
        low_classes = has_low_sample_count(scores, min_n=30)
        assert "pattern" in low_classes
        assert "texture" in low_classes
        assert "color" not in low_classes


class TestANOVA:
    def test_perform_anova_basic(self):
        # Create groups with different means to ensure non-zero F-stat
        scores = {
            "color": [0.1] * 30,
            "pattern": [0.5] * 30,
            "texture": [0.9] * 30
        }
        f_stat, p_val = perform_anova(scores)
        assert f_stat > 0
        assert 0 < p_val < 1

    def test_perform_anova_two_groups(self):
        scores = {
            "group_a": [1.0, 2.0, 3.0],
            "group_b": [4.0, 5.0, 6.0]
        }
        f_stat, p_val = perform_anova(scores)
        assert f_stat > 0
        assert 0 < p_val < 1

    def test_perform_anova_single_group_error(self):
        scores = {"only_group": [1.0, 2.0, 3.0]}
        with pytest.raises(ValueError, match="at least 2 groups"):
            perform_anova(scores)

    def test_perform_anova_empty_group_error(self):
        scores = {
            "group_a": [1.0, 2.0],
            "group_b": []
        }
        with pytest.raises(ValueError, match="At least 2 classes must have non-zero samples"):
            perform_anova(scores)


class TestBonferroniCorrection:
    def test_bonferroni_basic(self):
        p_values = [0.01, 0.03, 0.05, 0.10]
        results = bonferroni_correction(p_values, alpha=0.05)
        
        assert len(results) == 4
        for i, res in enumerate(results):
            assert res["test_index"] == i
            assert res["raw_p_value"] == p_values[i]
            assert res["adjusted_p_value"] == min(p_values[i] * 4, 1.0)
            assert res["adjusted_alpha"] == 0.05 / 4
            assert res["is_significant"] == (res["adjusted_p_value"] < 0.05)

    def test_bonferroni_empty_list(self):
        results = bonferroni_correction([], alpha=0.05)
        assert results == []

    def test_bonferroni_single_value(self):
        results = bonferroni_correction([0.01], alpha=0.05)
        assert len(results) == 1
        assert results[0]["adjusted_p_value"] == 0.01
        assert results[0]["is_significant"] is True


class TestAnalyzeSignificance:
    def test_analyze_significance_normal(self):
        scores = {
            "color": [0.1] * 50,
            "pattern": [0.5] * 50,
            "texture": [0.9] * 50
        }
        result = analyze_significance(scores, alpha=0.05)
        
        assert "sample_size_checks" in result
        assert "low_sample_classes" in result
        assert "anova_results" in result
        assert "bonferroni_results" in result
        assert "overall_significant" in result
        
        assert result["low_sample_classes"] == []
        assert result["anova_results"]["f_statistic"] > 0
        assert 0 < result["anova_results"]["p_value"] < 1

    def test_analyze_significance_low_sample_warning(self):
        scores = {
            "color": [0.1] * 50,
            "pattern": [0.5] * 5,
            "texture": [0.9] * 5
        }
        result = analyze_significance(scores, alpha=0.05)
        
        assert "pattern" in result["low_sample_classes"]
        assert "texture" in result["low_sample_classes"]
        assert "warning" in result
        assert "Low sample count" in result["warning"]

    def test_analyze_significance_single_class(self):
        scores = {"only": [0.1] * 50}
        result = analyze_significance(scores, alpha=0.05)
        
        assert "anova_error" in result
        assert "ANOVA could not be performed" in result["warning"]


class TestRunPipeline:
    def test_run_pipeline_creates_output_file(self):
        # Create temporary input file
        input_data = {
            "color": [0.1, 0.2, 0.3, 0.4, 0.5] * 10,
            "pattern": [0.3, 0.4, 0.5, 0.6, 0.7] * 10,
            "texture": [0.5, 0.6, 0.7, 0.8, 0.9] * 10
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input_scores.json"
            output_path = Path(tmpdir) / "output_results.json"
            
            with open(input_path, 'w') as f:
                json.dump(input_data, f)
            
            run_pipeline(str(input_path), str(output_path), alpha=0.05)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                results = json.load(f)
            
            assert "anova_results" in results
            assert "overall_significant" in results
            assert results["num_classes"] == 3

    def test_run_pipeline_file_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.json"
            with pytest.raises(FileNotFoundError):
                run_pipeline("/nonexistent/path.json", str(output_path))

    def test_run_pipeline_empty_data(self):
        input_data = {}
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.json"
            output_path = Path(tmpdir) / "output.json"
            
            with open(input_path, 'w') as f:
                json.dump(input_data, f)
            
            with pytest.raises(ValueError, match="No valid score data"):
                run_pipeline(str(input_path), str(output_path))

    def test_run_pipeline_list_format_input(self):
        # Test with list of records format
        input_data = [
            {"class": "color", "score": 0.1},
            {"class": "color", "score": 0.2},
            {"class": "pattern", "score": 0.5},
            {"class": "pattern", "score": 0.6}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.json"
            output_path = Path(tmpdir) / "output.json"
            
            with open(input_path, 'w') as f:
                json.dump(input_data, f)
            
            run_pipeline(str(input_path), str(output_path))
            
            with open(output_path, 'r') as f:
                results = json.load(f)
            
            assert results["num_classes"] == 2
            assert "color" in results["sample_size_checks"]
            assert "pattern" in results["sample_size_checks"]
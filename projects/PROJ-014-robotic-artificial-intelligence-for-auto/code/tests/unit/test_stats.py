"""
Unit tests for statistical analysis module.
"""
import pytest
import numpy as np
import json
import tempfile
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from analysis.stats import (
    calculate_descriptive_statistics,
    check_normality,
    check_homogeneity_of_variance,
    welchs_anova,
    kruskal_wallis,
    tukey_post_hoc,
    dunn_post_hoc,
    run_statistical_analysis,
    load_metrics_from_json
)


class TestDescriptiveStatistics:
    def test_basic_statistics(self):
        data = {
            "A": [1, 2, 3, 4, 5],
            "B": [10, 20, 30, 40, 50]
        }
        stats = calculate_descriptive_statistics(data)
        assert stats["A"]["mean"] == 3.0
        assert stats["A"]["count"] == 5
        assert stats["B"]["mean"] == 30.0
        assert stats["B"]["max"] == 50.0

    def test_empty_group(self):
        data = {"A": []}
        stats = calculate_descriptive_statistics(data)
        assert np.isnan(stats["A"]["mean"])
        assert stats["A"]["count"] == 0


class TestNormalityCheck:
    def test_normal_distribution(self):
        # Generate normal data
        data = {"A": np.random.normal(0, 1, 50).tolist()}
        is_normal, results = check_normality(data)
        # With 50 samples, it might pass or fail depending on randomness, but structure should be correct
        assert "A" in results
        assert isinstance(results["A"], bool)

    def test_small_sample(self):
        data = {"A": [1, 2]}
        is_normal, results = check_normality(data)
        assert results["A"] is False  # < 3 samples fails


class TestHomogeneityCheck:
    def test_homogeneous_variance(self):
        data = {
            "A": np.random.normal(0, 1, 30).tolist(),
            "B": np.random.normal(0, 1, 30).tolist()
        }
        is_homogeneous, stat, p_val = check_homogeneity_of_variance(data)
        assert isinstance(is_homogeneous, bool)
        assert isinstance(stat, float)
        assert isinstance(p_val, float)

    def test_insufficient_groups(self):
        data = {"A": [1, 2, 3]}
        is_homogeneous, stat, p_val = check_homogeneity_of_variance(data)
        assert is_homogeneous is True
        assert np.isnan(stat)


class TestWelchsAnova:
    def test_significant_difference(self):
        # Create two groups with different means
        data = {
            "A": [1, 2, 3, 4, 5],
            "B": [10, 11, 12, 13, 14]
        }
        result = welchs_anova(data)
        assert "f_statistic" in result
        assert "p_value" in result
        assert result["method"] == "welch_anova"
        # With such different means, p-value should be very small
        assert result["p_value"] < 0.05

    def test_insufficient_data(self):
        data = {"A": [1, 2, 3]}
        result = welchs_anova(data)
        assert result["method"] == "insufficient_data"


class TestKruskalWallis:
    def test_significant_difference(self):
        data = {
            "A": [1, 2, 3, 4, 5],
            "B": [10, 11, 12, 13, 14]
        }
        result = kruskal_wallis(data)
        assert "h_statistic" in result
        assert "p_value" in result
        assert result["method"] == "kruskal_wallis"
        assert result["p_value"] < 0.05

    def test_insufficient_data(self):
        data = {"A": [1, 2, 3]}
        result = kruskal_wallis(data)
        assert result["method"] == "insufficient_data"


class TestTukeyPostHoc:
    def test_pairwise_comparisons(self):
        data = {
            "A": [1, 2, 3, 4, 5],
            "B": [10, 11, 12, 13, 14],
            "C": [20, 21, 22, 23, 24]
        }
        result = tukey_post_hoc(data)
        assert "comparisons" in result
        assert len(result["comparisons"]) >= 2  # At least A-B, B-C, A-C
        assert result["method"] == "tukey_hsd"

    def test_insufficient_groups(self):
        data = {"A": [1, 2, 3]}
        result = tukey_post_hoc(data)
        assert result["method"] == "insufficient_data"


class TestDunnPostHoc:
    def test_pairwise_comparisons(self):
        data = {
            "A": [1, 2, 3, 4, 5],
            "B": [10, 11, 12, 13, 14]
        }
        result = dunn_post_hoc(data)
        assert "comparisons" in result
        assert len(result["comparisons"]) == 1
        assert result["method"] == "dunn_bonferroni"

    def test_insufficient_groups(self):
        data = {"A": [1, 2, 3]}
        result = dunn_post_hoc(data)
        assert result["method"] == "insufficient_data"


class TestRunStatisticalAnalysis:
    def test_full_pipeline(self):
        data = {
            "RGB": [0.8, 0.85, 0.9, 0.82, 0.88],
            "Depth": [0.6, 0.65, 0.7, 0.62, 0.68],
            "Grid": [0.7, 0.75, 0.8, 0.72, 0.78]
        }
        report = run_statistical_analysis(data)

        assert "header" in report
        assert "methodology" in report
        assert "descriptive_statistics" in report
        assert "statistical_tests" in report
        assert "post_hoc_tests" in report
        assert report["header"]["note"] == "Findings are associational, not causal."

class TestLoadMetricsFromJson:
    def test_load_from_file(self):
        # Create a temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "modalities": {
                    "RGB": {"auc": [0.8, 0.85, 0.9]},
                    "Depth": {"auc": [0.6, 0.65, 0.7]}
                }
            }, f)
            temp_path = f.name

        try:
            data = load_metrics_from_json(temp_path, "auc")
            assert "RGB" in data
            assert "Depth" in data
            assert data["RGB"] == [0.8, 0.85, 0.9]
        finally:
            os.unlink(temp_path)
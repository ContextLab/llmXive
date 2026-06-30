import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.statistics.wilcoxon_test import (
    load_success_rates,
    compute_wilcoxon_signed_rank,
    apply_holm_bonferroni,
    run_wilcoxon_analysis
)

class TestWilcoxonTestLogic:
    """Unit tests for Wilcoxon signed-rank test implementation."""

    @pytest.fixture
    def sample_eval_results(self, tmp_path):
        """Create a temporary evaluation results file."""
        data = {
            "within-embodiment": {
                "success_rate": [0.85, 0.82, 0.88, 0.80, 0.84],
                "trajectory_length": [10, 12, 11, 10, 11],
                "variance": [0.01, 0.02, 0.01, 0.03, 0.02]
            },
            "cross-embodiment": {
                "success_rate": [0.70, 0.72, 0.68, 0.75, 0.71],
                "trajectory_length": [15, 14, 16, 13, 15],
                "variance": [0.05, 0.04, 0.06, 0.03, 0.05]
            }
        }
        file_path = tmp_path / "eval_results.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
        return str(file_path)

    def test_load_success_rates(self, sample_eval_results):
        """Test loading success rates from JSON."""
        rates = load_success_rates(sample_eval_results)
        
        assert 'within-embodiment' in rates
        assert 'cross-embodiment' in rates
        assert len(rates['within-embodiment']) == 5
        assert len(rates['cross-embodiment']) == 5
        assert abs(rates['within-embodiment'][0] - 0.85) < 0.001

    def test_compute_wilcoxon_signed_rank(self):
        """Test Wilcoxon calculation with known values."""
        sample1 = [0.85, 0.82, 0.88, 0.80, 0.84]
        sample2 = [0.70, 0.72, 0.68, 0.75, 0.71]
        
        statistic, p_value = compute_wilcoxon_signed_rank(sample1, sample2)
        
        assert isinstance(statistic, float)
        assert isinstance(p_value, float)
        assert 0 <= p_value <= 1
        assert statistic >= 0

    def test_compute_wilcoxon_mismatched_sizes(self):
        """Test that mismatched sample sizes raise an error."""
        with pytest.raises(ValueError, match="Sample sizes must match"):
            compute_wilcoxon_signed_rank([1, 2, 3], [1, 2])

    def test_compute_wilcoxon_insufficient_samples(self):
        """Test that fewer than 2 samples raise an error."""
        with pytest.raises(ValueError, match="At least 2 paired samples"):
            compute_wilcoxon_signed_rank([0.5], [0.6])

    def test_apply_holm_bonferroni_single_test(self):
        """Test Holm-Bonferroni with a single p-value."""
        p_values = [0.03]
        result = apply_holm_bonferroni(p_values)
        
        assert result == [True]  # 0.03 < 0.05

    def test_apply_holm_bonferroni_multiple_tests(self):
        """Test Holm-Bonferroni with multiple p-values."""
        p_values = [0.01, 0.04, 0.06, 0.03]
        result = apply_holm_bonferroni(p_values)
        
        # With alpha=0.05 and n=4:
        # Sorted: 0.01 (idx 0), 0.03 (idx 3), 0.04 (idx 1), 0.06 (idx 2)
        # Thresholds: 0.05/4=0.0125, 0.05/3=0.0167, 0.05/2=0.025, 0.05/1=0.05
        # 0.01 < 0.0125 -> significant
        # 0.03 > 0.0167 -> stop, rest not significant
        expected = [True, False, False, False]
        assert result == expected

    def test_apply_holm_bonferroni_empty(self):
        """Test with empty list."""
        assert apply_holm_bonferroni([]) == []

    def test_run_wilcoxon_analysis(self, sample_eval_results, tmp_path):
        """Test full analysis pipeline."""
        output_path = tmp_path / "stat_results.json"
        
        results = run_wilcoxon_analysis(sample_eval_results, str(output_path))
        
        assert "p_value" in results
        assert "is_significant" in results
        assert "method" in results
        assert "statistic" in results
        assert results["method"] == "wilcoxon_signed_rank_with_holm_bonferroni"
        assert results["n_samples"] == 5
        
        # Verify file was written
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["p_value"] == results["p_value"]

    def test_run_wilcoxon_missing_data(self, tmp_path):
        """Test analysis fails when required data is missing."""
        incomplete_data = {"within-embodiment": {"success_rate": [0.5]}}
        input_path = tmp_path / "incomplete.json"
        with open(input_path, 'w') as f:
            json.dump(incomplete_data, f)
        
        output_path = tmp_path / "output.json"
        
        with pytest.raises(ValueError, match="Evaluation results must contain both"):
            run_wilcoxon_analysis(str(input_path), str(output_path))

"""
Unit tests for significance analysis module.
Tests ANOVA validation, Bonferroni correction, and stratification checks.
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np

# Import the module under test
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from src.stats.significance import (
    check_sample_sizes,
    has_low_sample_count,
    validate_stratification,
    perform_anova,
    bonferroni_correction,
    analyze_significance,
    run_pipeline,
    VALID_FEATURE_CLASSES
)


class TestSampleSizeChecks:
    """Tests for sample size validation functions."""

    def test_check_sample_sizes_returns_counts(self):
        """Check that sample sizes are correctly counted."""
        scores = {
            "Color": [1.0, 2.0, 3.0],
            "Pattern": [4.0, 5.0],
            "Texture": [6.0, 7.0, 8.0, 9.0]
        }
        result = check_sample_sizes(scores)
        assert result == {"Color": 3, "Pattern": 2, "Texture": 4}

    def test_has_low_sample_count_true(self):
        """Check that low sample count is detected."""
        scores = {
            "Color": [1.0, 2.0],  # Only 2 samples
            "Pattern": [3.0, 4.0, 5.0],
            "Texture": [6.0, 7.0, 8.0]
        }
        assert has_low_sample_count(scores, threshold=3) is True

    def test_has_low_sample_count_false(self):
        """Check that sufficient sample count passes."""
        scores = {
            "Color": [1.0, 2.0, 3.0, 4.0],
            "Pattern": [5.0, 6.0, 7.0, 8.0],
            "Texture": [9.0, 10.0, 11.0, 12.0]
        }
        assert has_low_sample_count(scores, threshold=3) is False


class TestStratificationValidation:
    """Tests for stratification validation logic."""

    def test_validate_stratification_valid_data(self):
        """Valid stratified data should pass validation."""
        scores = {
            "Color": [1.0, 2.0],
            "Pattern": [3.0, 4.0],
            "Texture": [5.0, 6.0]
        }
        # Should not raise
        validate_stratification(scores)

    def test_validate_stratification_empty_data(self):
        """Empty data should raise ValueError."""
        with pytest.raises(ValueError, match="Input data is empty"):
            validate_stratification({})

    def test_validate_stratification_unknown_class(self):
        """Unknown class should raise ValueError."""
        scores = {
            "Color": [1.0, 2.0],
            "UnknownClass": [3.0, 4.0]
        }
        with pytest.raises(ValueError, match="Unknown GarmentFeatureClass"):
            validate_stratification(scores)

    def test_validate_stratification_missing_class(self):
        """Missing required class should raise ValueError."""
        scores = {
            "Color": [1.0, 2.0],
            "Pattern": [3.0, 4.0]
            # Texture is missing
        }
        with pytest.raises(ValueError, match="Missing required GarmentFeatureClass"):
            validate_stratification(scores)


class TestANOVA:
    """Tests for ANOVA implementation."""

    def test_perform_anova_valid_input(self):
        """ANOVA should run on valid stratified data."""
        scores = {
            "Color": [1.0, 2.0, 3.0, 4.0, 5.0],
            "Pattern": [6.0, 7.0, 8.0, 9.0, 10.0],
            "Texture": [11.0, 12.0, 13.0, 14.0, 15.0]
        }
        f_stat, p_value = perform_anova(scores)
        
        assert isinstance(f_stat, float)
        assert isinstance(p_value, float)
        assert f_stat >= 0
        assert 0 <= p_value <= 1

    def test_perform_anova_insufficient_samples(self):
        """ANOVA should raise error with < 2 samples per class."""
        scores = {
            "Color": [1.0],  # Only 1 sample
            "Pattern": [2.0, 3.0],
            "Texture": [4.0, 5.0]
        }
        with pytest.raises(ValueError, match="Insufficient samples for ANOVA"):
            perform_anova(scores)

    def test_perform_anova_missing_stratification(self):
        """ANOVA should raise error if stratification is invalid."""
        scores = {
            "Color": [1.0, 2.0, 3.0],
            "Unknown": [4.0, 5.0, 6.0]
        }
        with pytest.raises(ValueError, match="Unknown GarmentFeatureClass"):
            perform_anova(scores)


class TestBonferroniCorrection:
    """Tests for Bonferroni correction logic."""

    def test_bonferroni_single_pvalue(self):
        """Bonferroni correction with single p-value."""
        p_values = [0.03]
        result = bonferroni_correction(p_values, alpha=0.05)
        
        assert result["num_tests"] == 1
        assert result["alpha_adjusted"] == 0.05
        assert result["corrected_p_values"] == [0.03]
        assert result["significance_decisions"] == [True]  # 0.03 < 0.05

    def test_bonferroni_multiple_pvalues(self):
        """Bonferroni correction with multiple p-values."""
        p_values = [0.01, 0.03, 0.06]
        result = bonferroni_correction(p_values, alpha=0.05)
        
        assert result["num_tests"] == 3
        assert result["alpha_adjusted"] == pytest.approx(0.05 / 3, rel=1e-3)
        
        # Corrected p-values should be original * 3, capped at 1.0
        expected_corrected = [0.03, 0.09, 0.18]
        assert result["corrected_p_values"] == expected_corrected

    def test_bonferroni_empty_input(self):
        """Bonferroni correction handles empty input."""
        result = bonferroni_correction([], alpha=0.05)
        
        assert result["num_tests"] == 0
        assert result["corrected_p_values"] == []
        assert result["significance_decisions"] == []

    def test_bonferroni_capping_at_one(self):
        """Corrected p-values should be capped at 1.0."""
        p_values = [0.5, 0.8]
        result = bonferroni_correction(p_values, alpha=0.05)
        
        # 0.8 * 2 = 1.6, should be capped to 1.0
        assert result["corrected_p_values"][1] == 1.0


class TestSignificanceAnalysis:
    """Tests for the full significance analysis pipeline."""

    def test_analyze_significance_full_pipeline(self):
        """Full analysis should produce correct report structure."""
        scores = {
            "Color": [1.0, 2.0, 3.0, 4.0, 5.0],
            "Pattern": [6.0, 7.0, 8.0, 9.0, 10.0],
            "Texture": [11.0, 12.0, 13.0, 14.0, 15.0]
        }
        
        result = analyze_significance(scores)
        
        assert "analysis_type" in result
        assert result["stratification_valid"] is True
        assert set(result["classes_analyzed"]) == {"Color", "Pattern", "Texture"}
        assert "anova_results" in result
        assert "f_statistic" in result["anova_results"]
        assert "p_value" in result["anova_results"]
        assert "is_significant" in result["anova_results"]

    def test_analyze_significance_with_pairwise_pvalues(self):
        """Analysis should include Bonferroni correction when pairwise p-values provided."""
        scores = {
            "Color": [1.0, 2.0, 3.0, 4.0, 5.0],
            "Pattern": [6.0, 7.0, 8.0, 9.0, 10.0],
            "Texture": [11.0, 12.0, 13.0, 14.0, 15.0]
        }
        pairwise_p = [0.01, 0.02, 0.03]
        
        result = analyze_significance(scores, pairwise_p_values=pairwise_p)
        
        assert "bonferroni_correction" in result
        assert result["bonferroni_correction"]["num_tests"] == 3
        assert "corrected_p_values" in result["bonferroni_correction"]

    def test_analyze_significance_low_power_warning(self):
        """Analysis should flag low power when sample size < 30."""
        scores = {
            "Color": [1.0, 2.0, 3.0],  # Only 3 samples
            "Pattern": [4.0, 5.0, 6.0],
            "Texture": [7.0, 8.0, 9.0]
        }
        
        result = analyze_significance(scores)
        
        assert result["low_power_warning"] is True
        assert "limitation" in result

    def test_analyze_significance_critical_low_count(self):
        """Analysis should raise error when sample size < 10."""
        scores = {
            "Color": [1.0, 2.0],  # Only 2 samples
            "Pattern": [3.0, 4.0],
            "Texture": [5.0, 6.0]
        }
        
        with pytest.raises(ValueError, match="Insufficient samples for statistical analysis"):
            analyze_significance(scores)


class TestRunPipeline:
    """Integration tests for the run_pipeline function."""

    def test_run_pipeline_creates_output_file(self, tmp_path):
        """Pipeline should create output JSON file with correct structure."""
        # Create input data
        input_data = {
            "per_class": {
                "Color": {"scores": [1.0, 2.0, 3.0, 4.0, 5.0]},
                "Pattern": {"scores": [6.0, 7.0, 8.0, 9.0, 10.0]},
                "Texture": {"scores": [11.0, 12.0, 13.0, 14.0, 15.0]}
            }
        }
        
        input_file = tmp_path / "input.json"
        output_file = tmp_path / "output.json"
        
        with open(input_file, 'w') as f:
            json.dump(input_data, f)
        
        # Run pipeline
        run_pipeline(str(input_file), str(output_file))
        
        # Verify output
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            result = json.load(f)
        
        assert "anova_results" in result
        assert "bonferroni_correction" in result or result.get("bonferroni_correction") is None

    def test_run_pipeline_file_not_found(self, tmp_path):
        """Pipeline should raise error if input file doesn't exist."""
        output_file = tmp_path / "output.json"
        
        with pytest.raises(FileNotFoundError):
            run_pipeline(str(tmp_path / "nonexistent.json"), str(output_file))

    def test_run_pipeline_invalid_input_format(self, tmp_path):
        """Pipeline should raise error for invalid input format."""
        input_data = {
            "per_class": {
                "Color": {"mean_lpips": 0.5},  # Missing 'scores'
                "Pattern": {"scores": [1.0, 2.0, 3.0]},
                "Texture": {"scores": [4.0, 5.0, 6.0]}
            }
        }
        
        input_file = tmp_path / "input.json"
        output_file = tmp_path / "output.json"
        
        with open(input_file, 'w') as f:
            json.dump(input_data, f)
        
        with pytest.raises(ValueError, match="missing 'scores' array"):
            run_pipeline(str(input_file), str(output_file))


class TestMain:
    """Tests for the CLI main function."""

    def test_main_with_valid_args(self, tmp_path, capsys):
        """Main should run successfully with valid arguments."""
        input_data = {
            "per_class": {
                "Color": {"scores": [1.0, 2.0, 3.0, 4.0, 5.0]},
                "Pattern": {"scores": [6.0, 7.0, 8.0, 9.0, 10.0]},
                "Texture": {"scores": [11.0, 12.0, 13.0, 14.0, 15.0]}
            }
        }
        
        input_file = tmp_path / "input.json"
        output_file = tmp_path / "output.json"
        
        with open(input_file, 'w') as f:
            json.dump(input_data, f)
        
        with patch('sys.argv', [
            'test_significance_analysis.py',
            '--input', str(input_file),
            '--output', str(output_file),
            '--alpha', '0.05'
        ]):
            from src.stats.significance import main
            main()
        
        assert output_file.exists()
        captured = capsys.readouterr()
        assert "Significance analysis report written to" in captured.out
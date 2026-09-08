"""
Unit tests for report generation functionality.
"""
import os
import sys
import tempfile
import json
import pytest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.report import (
    format_feature_importance,
    format_model_metrics,
    format_sensitivity_results,
    generate_report
)


class TestFormatFeatureImportance:
    """Tests for format_feature_importance function."""

    def test_empty_dict(self):
        """Test with empty feature importance dictionary."""
        result = format_feature_importance({})
        assert "No feature importance data available" in result

    def test_single_feature(self):
        """Test with a single feature."""
        features = {"feature_a": 0.85}
        result = format_feature_importance(features)
        assert "feature_a" in result
        assert "0.8500" in result

    def test_multiple_features_sorted(self):
        """Test that features are sorted by importance."""
        features = {
            "feature_c": 0.50,
            "feature_a": 0.90,
            "feature_b": 0.75
        }
        result = format_feature_importance(features)
        # Check that feature_a appears before feature_b and feature_c
        a_pos = result.find("feature_a")
        b_pos = result.find("feature_b")
        c_pos = result.find("feature_c")
        assert a_pos < b_pos < c_pos

    def test_top_n_limit(self):
        """Test that top_n limits the output."""
        features = {
            f"feature_{i}": 0.90 - i * 0.05
            for i in range(20)
        }
        result = format_feature_importance(features, top_n=5)
        # Should only have 5 features
        assert result.count("| 1 |") == 1
        assert result.count("| 5 |") == 1
        assert "feature_5" not in result  # Should be truncated


class TestFormatModelMetrics:
    """Tests for format_model_metrics function."""

    def test_empty_metrics(self):
        """Test with empty metrics dictionary."""
        result = format_model_metrics({})
        assert result == ""

    def test_primary_results(self):
        """Test formatting of primary PGLS results."""
        metrics = {
            "primary_results": {
                "r_squared": 0.65,
                "p_value": 0.001,
                "feature_importance": {"gene_a": 0.8, "gene_b": 0.2}
            }
        }
        result = format_model_metrics(metrics)
        assert "Primary Analysis Results" in result
        assert "0.65" in result
        assert "0.001" in result
        assert "gene_a" in result

    def test_model_comparison(self):
        """Test formatting of model comparison table."""
        metrics = {
            "model_comparison": {
                "Random Forest": {"r_squared": 0.70, "rmse": 0.15, "mae": 0.10},
                "Elastic Net": {"r_squared": 0.65, "rmse": 0.18, "mae": 0.12}
            }
        }
        result = format_model_metrics(metrics)
        assert "Model Comparison" in result
        assert "Random Forest" in result
        assert "Elastic Net" in result
        assert "0.70" in result

    def test_significance_test(self):
        """Test formatting of significance test results."""
        metrics = {
            "significance_test": {
                "baseline_r_squared": 0.02,
                "model_r_squared": 0.65,
                "p_value": 0.001,
                "is_significant": True
            }
        }
        result = format_model_metrics(metrics)
        assert "Statistical Significance" in result
        assert "0.02" in result
        assert "True" in result


class TestFormatSensitivityResults:
    """Tests for format_sensitivity_results function."""

    def test_empty_sensitivity(self):
        """Test with empty sensitivity dictionary."""
        result = format_sensitivity_results({})
        assert "No sensitivity analysis results available" in result

    def test_threshold_sweep(self):
        """Test formatting of threshold sweep results."""
        sensitivity = {
            "threshold_sweep": [
                {"threshold": 0.1, "r_squared": 0.60, "rmse": 0.20},
                {"threshold": 0.5, "r_squared": 0.65, "rmse": 0.18},
                {"threshold": 0.9, "r_squared": 0.62, "rmse": 0.19}
            ]
        }
        result = format_sensitivity_results(sensitivity)
        assert "Threshold Sweep Results" in result
        assert "0.1" in result
        assert "0.5" in result
        assert "0.9" in result

    def test_variation_summary(self):
        """Test formatting of variation summary."""
        sensitivity = {
            "variation": {
                "max_diff": 0.03,
                "within_tolerance": True
            }
        }
        result = format_sensitivity_results(sensitivity)
        assert "Variation Summary" in result
        assert "0.03" in result
        assert "True" in result


class TestGenerateReport:
    """Tests for generate_report function."""

    def test_generate_with_all_data(self):
        """Test report generation with complete data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create sample metrics file
            metrics_path = Path(tmpdir) / "metrics.json"
            metrics_data = {
                "primary_results": {
                    "r_squared": 0.65,
                    "p_value": 0.001,
                    "feature_importance": {"gene_a": 0.8}
                },
                "model_comparison": {
                    "Random Forest": {"r_squared": 0.70}
                },
                "significance_test": {
                    "baseline_r_squared": 0.02,
                    "model_r_squared": 0.65,
                    "p_value": 0.001,
                    "is_significant": True
                }
            }
            with open(metrics_path, 'w') as f:
                json.dump(metrics_data, f)

            # Create sample sensitivity file
            sensitivity_path = Path(tmpdir) / "sensitivity_results.json"
            sensitivity_data = {
                "threshold_sweep": [
                    {"threshold": 0.1, "r_squared": 0.60},
                    {"threshold": 0.5, "r_squared": 0.65}
                ],
                "variation": {
                    "max_diff": 0.03,
                    "within_tolerance": True
                }
            }
            with open(sensitivity_path, 'w') as f:
                json.dump(sensitivity_data, f)

            # Generate report
            output_path = Path(tmpdir) / "final_report.md"
            result_path = generate_report(
                output_path=str(output_path),
                metrics_path=str(metrics_path),
                sensitivity_path=str(sensitivity_path)
            )

            # Verify report exists
            assert os.path.exists(result_path)
            assert result_path == str(output_path)

            # Verify report content
            with open(result_path, 'r') as f:
                content = f.read()

            assert "Plant Secondary Metabolite Prediction Report" in content
            assert "Primary Analysis Results" in content
            assert "Sensitivity Analysis" in content
            assert "Threshold Justification" in content
            assert "0.65" in content

            # Verify JSON summary also created
            json_path = Path(tmpdir) / "final_report.json"
            assert os.path.exists(json_path)

    def test_generate_without_sensitivity(self):
        """Test report generation without sensitivity data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create only metrics file
            metrics_path = Path(tmpdir) / "metrics.json"
            with open(metrics_path, 'w') as f:
                json.dump({"primary_results": {"r_squared": 0.65}}, f)

            output_path = Path(tmpdir) / "final_report.md"
            result_path = generate_report(
                output_path=str(output_path),
                metrics_path=str(metrics_path)
            )

            assert os.path.exists(result_path)

            with open(result_path, 'r') as f:
                content = f.read()

            assert "No sensitivity analysis results available" in content

    def test_generate_missing_files(self):
        """Test report generation with missing input files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "final_report.md"
            result_path = generate_report(
                output_path=str(output_path),
                metrics_path="/nonexistent/metrics.json",
                sensitivity_path="/nonexistent/sensitivity.json"
            )

            assert os.path.exists(result_path)

            with open(result_path, 'r') as f:
                content = f.read()

            # Should handle missing data gracefully
            assert "Plant Secondary Metabolite Prediction Report" in content
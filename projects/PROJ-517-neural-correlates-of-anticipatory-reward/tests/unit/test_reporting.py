"""
Unit tests for the reporting module (T030).

Tests the generation of summary_report.txt with coefficient, p-value,
MDES, CV scores, and data loss metrics.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest

# Import the function to test
from reporting import generate_summary_report, load_json_file


class TestReportingModule:
    """Test cases for the reporting module."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory structure for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create required subdirectories
            (tmp_path / "processed").mkdir()
            (tmp_path / "raw").mkdir()
            (tmp_path / "figures").mkdir()
            
            yield tmp_path

    def test_generate_summary_report_creates_file(self, temp_data_dir):
        """Test that generate_summary_report creates the output file."""
        # Create mock validation report
        validation_data = {
            "ingestion_rows_total": 100,
            "ingestion_rows_valid": 95,
            "ingestion_rows_dropped": 5,
            "validation_status": "passed"
        }
        with open(temp_data_dir / "processed" / "validation_report.json", 'w') as f:
            json.dump(validation_data, f)

        # Create mock model results
        model_data = {
            "coefficient": 0.5,
            "p_value": 0.01,
            "model_family": "NegativeBinomial",
            "dispersion": 1.5,
            "cv_score_mean": 0.3,
            "cv_score_std": 0.05,
            "mdes_80_power": 0.2,
            "neuron_count": 2,
            "bonferroni_corrected_p": 0.02
        }
        with open(temp_data_dir / "processed" / "model_results.json", 'w') as f:
            json.dump(model_data, f)

        # Generate report
        output_path = temp_data_dir / "processed" / "summary_report.txt"
        result_path = generate_summary_report(temp_data_dir, output_path)

        # Assert file was created
        assert result_path.exists(), "Summary report file was not created"
        assert result_path == output_path, "Output path mismatch"

    def test_report_contains_required_metrics(self, temp_data_dir):
        """Test that the generated report contains all required metrics."""
        # Setup mock data
        validation_data = {
            "ingestion_rows_total": 100,
            "ingestion_rows_valid": 95,
            "ingestion_rows_dropped": 5,
            "validation_status": "passed"
        }
        with open(temp_data_dir / "processed" / "validation_report.json", 'w') as f:
            json.dump(validation_data, f)

        model_data = {
            "coefficient": 0.5,
            "p_value": 0.01,
            "model_family": "NegativeBinomial",
            "dispersion": 1.5,
            "cv_score_mean": 0.3,
            "cv_score_std": 0.05,
            "mdes_80_power": 0.2,
            "neuron_count": 2,
            "bonferroni_corrected_p": 0.02
        }
        with open(temp_data_dir / "processed" / "model_results.json", 'w') as f:
            json.dump(model_data, f)

        # Generate report
        output_path = temp_data_dir / "processed" / "summary_report.txt"
        generate_summary_report(temp_data_dir, output_path)

        # Read and verify content
        with open(output_path, 'r') as f:
            content = f.read()

        # Check for required sections and values
        assert "DATA QUALITY METRICS" in content, "Missing data quality section"
        assert "STATISTICAL MODEL RESULTS" in content, "Missing model results section"
        assert "POWER ANALYSIS" in content, "Missing power analysis section"
        assert "CROSS-VALIDATION RESULTS" in content, "Missing CV section"
        
        # Check for specific metric values
        assert "0.5" in content, "Coefficient value not found in report"
        assert "0.01" in content, "P-value not found in report"
        assert "0.2" in content, "MDES value not found in report"
        assert "0.3" in content, "CV score mean not found in report"
        assert "95" in content, "Valid rows count not found in report"
        assert "2" in content, "Neuron count not found in report"

    def test_report_handles_missing_validation_report(self, temp_data_dir):
        """Test that report generation handles missing validation report gracefully."""
        # Create only model results, no validation report
        model_data = {
            "coefficient": 0.5,
            "p_value": 0.01,
            "model_family": "Poisson",
            "dispersion": 1.0,
            "cv_score_mean": 0.3,
            "cv_score_std": 0.05,
            "mdes_80_power": 0.2,
            "neuron_count": 1,
            "bonferroni_corrected_p": 0.01
        }
        with open(temp_data_dir / "processed" / "model_results.json", 'w') as f:
            json.dump(model_data, f)

        # Generate report (should not raise exception)
        output_path = temp_data_dir / "processed" / "summary_report.txt"
        result_path = generate_summary_report(temp_data_dir, output_path)

        assert result_path.exists(), "Report should be generated even with missing validation data"

        with open(output_path, 'r') as f:
            content = f.read()
        
        # Should contain N/A for missing data
        assert "N/A" in content, "Report should indicate missing data with N/A"

    def test_report_handles_missing_model_results(self, temp_data_dir):
        """Test that report generation handles missing model results gracefully."""
        # Create only validation report, no model results
        validation_data = {
            "ingestion_rows_total": 100,
            "ingestion_rows_valid": 95,
            "ingestion_rows_dropped": 5,
            "validation_status": "passed"
        }
        with open(temp_data_dir / "processed" / "validation_report.json", 'w') as f:
            json.dump(validation_data, f)

        # Generate report (should not raise exception)
        output_path = temp_data_dir / "processed" / "summary_report.txt"
        result_path = generate_summary_report(temp_data_dir, output_path)

        assert result_path.exists(), "Report should be generated even with missing model data"

        with open(output_path, 'r') as f:
            content = f.read()
        
        # Should contain N/A for missing model data
        assert "N/A" in content, "Report should indicate missing model data with N/A"
        assert "model not run" in content, "Report should indicate model was not run"

    def test_significance_flagging(self, temp_data_dir):
        """Test that significance flags are correctly added to the report."""
        # Setup with significant p-value
        validation_data = {
            "ingestion_rows_total": 100,
            "ingestion_rows_valid": 95,
            "ingestion_rows_dropped": 5,
            "validation_status": "passed"
        }
        with open(temp_data_dir / "processed" / "validation_report.json", 'w') as f:
            json.dump(validation_data, f)

        model_data = {
            "coefficient": 0.5,
            "p_value": 0.001,  # Significant
            "model_family": "NegativeBinomial",
            "dispersion": 1.5,
            "cv_score_mean": 0.3,
            "cv_score_std": 0.05,
            "mdes_80_power": 0.2,
            "neuron_count": 1,
            "bonferroni_corrected_p": 0.001
        }
        with open(temp_data_dir / "processed" / "model_results.json", 'w') as f:
            json.dump(model_data, f)

        output_path = temp_data_dir / "processed" / "summary_report.txt"
        generate_summary_report(temp_data_dir, output_path)

        with open(output_path, 'r') as f:
            content = f.read()

        assert "STATISTICALLY SIGNIFICANT" in content, "Should flag significant result"
        assert "SIGNIFICANT AFTER CORRECTION" in content, "Should flag corrected significant result"

    def test_non_significant_flagging(self, temp_data_dir):
        """Test that non-significant results are correctly flagged."""
        validation_data = {
            "ingestion_rows_total": 100,
            "ingestion_rows_valid": 95,
            "ingestion_rows_dropped": 5,
            "validation_status": "passed"
        }
        with open(temp_data_dir / "processed" / "validation_report.json", 'w') as f:
            json.dump(validation_data, f)

        model_data = {
            "coefficient": 0.1,
            "p_value": 0.5,  # Not significant
            "model_family": "Poisson",
            "dispersion": 1.0,
            "cv_score_mean": 0.1,
            "cv_score_std": 0.02,
            "mdes_80_power": 0.3,
            "neuron_count": 1,
            "bonferroni_corrected_p": 0.5
        }
        with open(temp_data_dir / "processed" / "model_results.json", 'w') as f:
            json.dump(model_data, f)

        output_path = temp_data_dir / "processed" / "summary_report.txt"
        generate_summary_report(temp_data_dir, output_path)

        with open(output_path, 'r') as f:
            content = f.read()

        assert "Not significant" in content, "Should indicate non-significant result"
        assert "Not significant after correction" in content, "Should indicate non-significant after correction"

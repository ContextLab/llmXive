import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
# The API surface indicates: from src.evaluation.final_report import ..., main
from src.evaluation.final_report import (
    load_json_safe,
    load_yaml_safe,
    aggregate_results,
    generate_report,
    main
)

class TestFinalReport:
    """Unit tests for src/evaluation/final_report.py to verify required keys in the report."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test artifacts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_load_json_safe(self, temp_dir):
        """Test loading a valid JSON file."""
        test_file = temp_dir / "test.json"
        test_data = {"key": "value", "number": 42}
        with open(test_file, "w") as f:
            json.dump(test_data, f)

        result = load_json_safe(test_file)
        assert result == test_data

    def test_load_json_safe_missing_file(self, temp_dir):
        """Test loading a non-existent JSON file returns None."""
        missing_file = temp_dir / "missing.json"
        result = load_json_safe(missing_file)
        assert result is None

    def test_load_yaml_safe(self, temp_dir):
        """Test loading a valid YAML file."""
        test_file = temp_dir / "test.yaml"
        test_data = {"key": "value", "number": 42}
        with open(test_file, "w") as f:
            import yaml
            yaml.dump(test_data, f)

        result = load_yaml_safe(test_file)
        assert result == test_data

    def test_load_yaml_safe_missing_file(self, temp_dir):
        """Test loading a non-existent YAML file returns None."""
        missing_file = temp_dir / "missing.yaml"
        result = load_yaml_safe(missing_file)
        assert result is None

    def test_aggregate_results(self, temp_dir):
        """Test aggregating results from multiple files."""
        # Create mock result files
        stats_file = temp_dir / "stats.json"
        with open(stats_file, "w") as f:
            json.dump({"mean_success": 0.8, "p_value": 0.01}, f)

        linearity_file = temp_dir / "linearity.json"
        with open(linearity_file, "w") as f:
            json.dump({"correlation": 0.95, "valid": True}, f)

        results = aggregate_results(temp_dir)

        assert "stats" in results
        assert "linearity" in results
        assert results["stats"]["mean_success"] == 0.8
        assert results["linearity"]["correlation"] == 0.95

    def test_aggregate_results_missing_files(self, temp_dir):
        """Test aggregation when some files are missing."""
        results = aggregate_results(temp_dir)
        assert results == {}

    def test_generate_report_structure(self, temp_dir):
        """Test that generate_report produces the expected structure."""
        # Prepare mock results
        results = {
            "stats": {
                "mean_success_rate": 0.85,
                "bh_corrected_primary": [0.03],
                "bh_corrected_sensitivity": [0.12],
                "observed_success_rate_diff": 0.05
            },
            "linearity": {
                "correlation_coefficient": 0.92,
                "linearity_valid": True,
                "reconstruction_error": 0.02
            },
            "sensitivity": {
                "robustness_score": 0.88,
                "variance": 0.01
            },
            "latency": {
                "total_skill_selection_latency_ms": 150.5,
                "embedding_latency_ms": 50.2,
                "retrieval_latency_ms": 45.3,
                "interpolation_latency_ms": 55.0
            },
            "memory": {
                "peak_memory_mb": 2048,
                "fits_constraint": True
            },
            "power": {
                "estimated_power": 0.82,
                "power_sufficient": True
            }
        }

        output_file = temp_dir / "report.md"
        generate_report(results, output_file)

        assert output_file.exists()
        
        content = output_file.read_text()
        
        # Verify required sections exist
        assert "# Final Report: llmXive LatentSkill Extension" in content
        assert "## 1. Methodology" in content
        assert "## 2. Results" in content
        assert "## 3. Statistical Significance" in content
        assert "## 4. Limitations" in content

        # Verify specific metrics are included
        assert "0.85" in content  # mean_success_rate
        assert "0.92" in content  # correlation_coefficient
        assert "0.03" in content  # p-value
        assert "0.82" in content  # power

    def test_generate_report_with_missing_data(self, temp_dir):
        """Test report generation when some data is missing (null/None)."""
        results = {
            "stats": {
                "mean_success_rate": 0.85,
                "bh_corrected_primary": [],
                "bh_corrected_sensitivity": [],
                "observed_success_rate_diff": 0.05
            },
            "linearity": {
                "correlation_coefficient": None,
                "linearity_valid": None,
                "reconstruction_error": None
            },
            "sensitivity": {},
            "latency": {},
            "memory": {},
            "power": {}
        }

        output_file = temp_dir / "report.md"
        generate_report(results, output_file)

        assert output_file.exists()
        
        content = output_file.read_text()
        assert "## 1. Methodology" in content
        assert "## 4. Limitations" in content

    def test_main_cli_integration(self, temp_dir):
        """Test the main CLI function with command line arguments."""
        # Create mock result files
        stats_file = temp_dir / "stats_report.json"
        with open(stats_file, "w") as f:
            json.dump({"mean_success_rate": 0.85}, f)

        linearity_file = temp_dir / "linearity_validation.json"
        with open(linearity_file, "w") as f:
            json.dump({"correlation_coefficient": 0.92}, f)

        output_file = temp_dir / "final_report.md"

        # Mock sys.argv to simulate CLI call
        test_args = [
            "final_report.py",
            "--input_dir", str(temp_dir),
            "--output", str(output_file)
        ]

        with patch("sys.argv", test_args):
            main()

        assert output_file.exists()
        assert "# Final Report: llmXive LatentSkill Extension" in output_file.read_text()

    def test_required_keys_in_report(self, temp_dir):
        """Verify that the generated report contains all required keys from the spec."""
        # Create comprehensive mock results
        results = {
            "stats": {
                "mean_success_rate": 0.85,
                "bh_corrected_primary": [0.03],
                "bh_corrected_sensitivity": [0.12],
                "observed_success_rate_diff": 0.05
            },
            "linearity": {
                "correlation_coefficient": 0.92,
                "linearity_valid": True,
                "reconstruction_error": 0.02
            },
            "sensitivity": {
                "robustness_score": 0.88,
                "variance": 0.01
            },
            "latency": {
                "total_skill_selection_latency_ms": 150.5,
                "embedding_latency_ms": 50.2,
                "retrieval_latency_ms": 45.3,
                "interpolation_latency_ms": 55.0
            },
            "memory": {
                "peak_memory_mb": 2048,
                "fits_constraint": True
            },
            "power": {
                "estimated_power": 0.82,
                "power_sufficient": True
            }
        }

        output_file = temp_dir / "report.md"
        generate_report(results, output_file)

        content = output_file.read_text()

        # Check for critical metrics required by the spec
        required_indicators = [
            "Success Rate",
            "Latency",
            "Linearity",
            "Pearson",
            "correlation",
            "Statistical Significance",
            "p-values",
            "Benjamini-Hochberg",
            "Limitations",
            "Power Analysis",
            "Memory"
        ]

        for indicator in required_indicators:
            assert indicator in content, f"Required indicator '{indicator}' not found in report"

    def test_report_formatting(self, temp_dir):
        """Test that the report is properly formatted Markdown."""
        results = {
            "stats": {"mean_success_rate": 0.85},
            "linearity": {"correlation_coefficient": 0.92},
            "sensitivity": {},
            "latency": {},
            "memory": {},
            "power": {}
        }

        output_file = temp_dir / "report.md"
        generate_report(results, output_file)

        content = output_file.read_text()

        # Check for Markdown formatting elements
        assert content.startswith("# ")
        assert "## " in content
        assert "### " in content or "- " in content  # Either subheaders or lists
        assert content.endswith("\n")
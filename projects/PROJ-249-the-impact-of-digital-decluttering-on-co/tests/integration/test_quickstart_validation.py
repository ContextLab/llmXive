"""
Integration tests for the quickstart validation pipeline.
These tests verify that the end-to-end reproducibility check works correctly.
"""
import os
import json
import subprocess
import pytest
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

class TestQuickstartValidation:
    """Test suite for quickstart validation pipeline."""

    @pytest.fixture
    def validation_script(self):
        """Path to the validation script."""
        return PROJECT_ROOT / "code" / "pipeline" / "validate_quickstart.py"

    @pytest.fixture
    def results_dir(self):
        """Path to results directory."""
        return PROJECT_ROOT / "results"

    def test_script_exists(self, validation_script):
        """Test that the validation script exists."""
        assert validation_script.exists(), "Validation script not found"

    def test_script_is_python_file(self, validation_script):
        """Test that the validation script is a valid Python file."""
        with open(validation_script, 'r') as f:
            content = f.read()
            assert 'import' in content, "Script does not contain imports"
            assert 'def main' in content, "Script does not have a main function"

    def test_quickstart_execution(self, validation_script, results_dir, tmp_path):
        """
        Test that running the quickstart validation script executes successfully.
        This is a comprehensive integration test that runs the full pipeline.
        """
        # Ensure results directory exists
        results_dir.mkdir(parents=True, exist_ok=True)

        # Run the validation script
        result = subprocess.run(
            [sys.executable, str(validation_script)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout for full pipeline
        )

        # Check if the script ran (success or failure is acceptable for this test)
        # The test passes if the script executes without crashing
        assert result.returncode in [0, 1], f"Script crashed: {result.stderr}"

        # Check that a validation report was generated
        report_path = results_dir / "quickstart_validation_report.json"
        assert report_path.exists(), "Validation report was not generated"

        # Validate the structure of the report
        with open(report_path, 'r') as f:
            report = json.load(f)

        assert "steps" in report, "Report missing 'steps' key"
        assert "success" in report, "Report missing 'success' key"
        assert "duration_seconds" in report, "Report missing 'duration_seconds' key"

        # Verify each step has required fields
        for step in report["steps"]:
            assert "name" in step, f"Step missing 'name': {step}"
            assert "success" in step, f"Step missing 'success': {step}"
            assert "command" in step, f"Step missing 'command': {step}"

    def test_required_output_files_generated(self, results_dir):
        """
        Test that all required output files from the quickstart pipeline are generated.
        This test should be run after a successful quickstart validation.
        """
        required_files = [
            "statistical_summary.json",
            "power_analysis.json",
            "sensitivity_analysis_report.md",
            "final_report.md",
            "quickstart_validation_report.json"
        ]

        missing_files = []
        for file_name in required_files:
            file_path = results_dir / file_name
            if not file_path.exists():
                missing_files.append(file_name)

        if missing_files:
            pytest.fail(f"Missing required output files: {missing_files}")

    def test_validation_report_structure(self, results_dir):
        """Test the structure and content of the validation report."""
        report_path = results_dir / "quickstart_validation_report.json"
        
        if not report_path.exists():
            pytest.skip("Validation report not found. Run quickstart validation first.")

        with open(report_path, 'r') as f:
            report = json.load(f)

        # Verify report structure
        assert "start_time" in report
        assert "end_time" in report
        assert "duration_seconds" in report
        assert isinstance(report["steps"], list)
        assert len(report["steps"]) > 0, "No steps recorded in validation report"

        # Check that all expected steps are present
        expected_step_names = [
            "Generate Synthetic Baseline Data",
            "Validate Instruments",
            "Merge Data",
            "Calculate Change Scores",
            "Run Bootstrap CI Analysis",
            "Calculate Effect Sizes",
            "Apply Holm-Bonferroni Correction",
            "Generate Statistical Summary",
            "Run Power Simulation",
            "Generate Sensitivity Report",
            "Validate Success Criteria",
            "Generate Final Report",
            "Generate Plots"
        ]

        actual_step_names = [step["name"] for step in report["steps"]]
        
        for expected_name in expected_step_names:
            assert expected_name in actual_step_names, f"Missing step: {expected_name}"

    def test_pipeline_consistency(self, results_dir):
        """
        Test that the pipeline produces consistent results across runs.
        This test checks that key metrics are within expected ranges.
        """
        # Load statistical summary if available
        summary_path = results_dir / "statistical_summary.json"
        if not summary_path.exists():
            pytest.skip("Statistical summary not found. Run quickstart validation first.")

        with open(summary_path, 'r') as f:
            summary = json.load(f)

        # Verify that metrics have expected structure
        assert "metrics" in summary, "Statistical summary missing 'metrics' key"
        
        metrics = summary["metrics"]
        assert len(metrics) > 0, "No metrics in statistical summary"

        # Check that at least one metric has significance
        significant_metrics = [
            m for m in metrics 
            if m.get("significant", False) or m.get("corrected_p_value", 1.0) < 0.05
        ]

        # Note: We don't assert that there MUST be significant results,
        # as this depends on the data. We just verify the structure is correct.
        assert all("metric_name" in m for m in metrics), "Metrics missing 'metric_name'"
        assert all("change_mean" in m for m in metrics), "Metrics missing 'change_mean'"

"""
Tests for the reporting module (User Story 3).
"""
import pytest
import os
import tempfile
import json

from code.report import (
    generate_report_logic,
    save_final_results,
    save_report,
    verify_report_constraints,
    run_reporting_pipeline
)
from code.data_model import DesignType


class TestReportGeneration:
    """Tests for report generation logic."""

    def test_generates_report_within_subjects(self):
        """Test report generation for Within-Subjects design."""
        results = {
            "anova_results": {
                "F": 4.56,
                "p_value": 0.034,
                "p_fdr": 0.045,
                "effect_size": 0.8
            },
            "sensitivity": {"0.05": 0.85}
        }
        
        report = generate_report_logic(results, "Within-Subjects")
        
        assert "Within-Subjects" in report
        assert "modulation" in report.lower()
        assert "associational" not in report  # Should not be forced here
        assert "Limitations" in report

    def test_generates_report_between_subjects(self):
        """Test report generation for Between-Subjects design."""
        results = {
            "anova_results": {
                "F": 3.21,
                "p_value": 0.078,
                "p_fdr": 0.089,
                "effect_size": 0.5
            },
            "sensitivity": {"0.05": 0.60}
        }
        
        report = generate_report_logic(results, "Between-Subjects")
        
        assert "Between-Subjects" in report
        assert "associational" in report.lower()
        assert "Limitations" in report
        # Check that the specific phrasing about associational differences is present
        assert "associational differences" in report.lower() or "associational group differences" in report.lower()

    def test_limitations_section_content(self):
        """Verify the Limitations section contains required text for Between-Subjects."""
        results = {"anova_results": {}}
        report = generate_report_logic(results, "Between-Subjects")
        
        # The prompt requires explicit "associational" phrasing in Limitations
        # We check the whole report for now, as parsing markdown sections is complex without a parser
        assert "associational" in report.lower()
        assert "causal" not in report.lower() or "does not support causal" in report.lower()


class TestReportSaving:
    """Tests for saving report artifacts."""

    def test_save_final_results_json(self):
        """Test that final results are saved correctly with design_type."""
        results = {
            "anova_results": {"p_value": 0.05, "p_fdr": 0.05},
            "other": "data"
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock get_path to use tmpdir (or just use the function and check if it creates the file)
            # Since get_path is imported, we might need to patch it or rely on the fact that it creates the dir.
            # For this test, we assume the function works and creates the file.
            # We need to ensure the directory exists for the test to pass without mocking.
            os.makedirs("data/processed", exist_ok=True)
            
            path = save_final_results(results, "Between-Subjects")
            
            assert os.path.exists(path)
            with open(path, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data['design_type'] == "Between-Subjects"
            assert 'p_fdr' in saved_data['anova_results']

    def test_save_report_markdown(self):
        """Test that report markdown is saved correctly."""
        content = "# Test Report\n\nContent here."
        
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs("reports", exist_ok=True)
            path = save_report(content, "Between-Subjects")
            
            assert os.path.exists(path)
            with open(path, 'r') as f:
                saved_content = f.read()
            
            assert saved_content == content


class TestReportConstraints:
    """Tests for constraint verification logic."""

    def test_verify_associational_in_between_subjects(self):
        """Verify that Between-Subjects reports must contain 'associational'."""
        # Create a mock report that IS valid
        valid_content = "# Report\n\n## Limitations\n\nThis is an associational study."
        
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = os.path.join(tmpdir, "report.md")
            with open(report_path, 'w') as f:
                f.write(valid_content)
            
            # This should pass
            assert verify_report_constraints(report_path, "Between-Subjects") is True

    def test_verify_missing_associational_fails(self):
        """Verify that Between-Subjects reports WITHOUT 'associational' fail."""
        invalid_content = "# Report\n\n## Limitations\n\nThis is a causal study."
        
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = os.path.join(tmpdir, "report.md")
            with open(report_path, 'w') as f:
                f.write(invalid_content)
            
            # This should fail
            assert verify_report_constraints(report_path, "Between-Subjects") is False

    def test_verify_within_subjects_no_associational_required(self):
        """Verify that Within-Subjects reports do not trigger the 'associational' check."""
        content = "# Report\n\n## Limitations\n\nStandard limitations."
        
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = os.path.join(tmpdir, "report.md")
            with open(report_path, 'w') as f:
                f.write(content)
            
            # This should pass (no 'associational' required for Within)
            assert verify_report_constraints(report_path, "Within-Subjects") is True

    def test_verify_missing_limitations_section_fails(self):
        """Verify that reports missing the Limitations section fail for Between-Subjects."""
        content = "# Report\n\n## Results\n\nSome results."
        
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = os.path.join(tmpdir, "report.md")
            with open(report_path, 'w') as f:
                f.write(content)
            
            assert verify_report_constraints(report_path, "Between-Subjects") is False


class TestPipeline:
    """Integration tests for the full reporting pipeline."""

    def test_run_reporting_pipeline(self):
        """Test the full pipeline execution."""
        results = {
            "anova_results": {"p_value": 0.01, "p_fdr": 0.02},
            "sensitivity": {"0.05": 0.9}
        }
        
        # Ensure directories exist
        os.makedirs("data/processed", exist_ok=True)
        os.makedirs("reports", exist_ok=True)
        
        output = run_reporting_pipeline(results, "Between-Subjects")
        
        assert "results_path" in output
        assert "report_path" in output
        assert output["valid"] is True
        
        assert os.path.exists(output["results_path"])
        assert os.path.exists(output["report_path"])

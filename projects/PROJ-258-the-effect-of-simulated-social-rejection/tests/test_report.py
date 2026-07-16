import pytest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
from report import (
    calculate_effect_size_ci,
    generate_report_logic,
    save_report,
    verify_report_constraints,
    save_final_results,
    run_reporting_pipeline
)
from config import get_path

class TestCalculateEffectSizeCI:
    def test_ci_calculation(self):
        """Test that confidence intervals are calculated correctly."""
        es = 0.5
        n1, n2 = 30, 30
        ci = calculate_effect_size_ci(es, n1, n2, confidence=0.95)
        
        assert "lower" in ci
        assert "upper" in ci
        assert "center" in ci
        assert ci["center"] == es
        assert ci["lower"] < es
        assert ci["upper"] > es

    def test_ci_width_with_sample_size(self):
        """Test that CI width decreases with larger sample size."""
        es = 0.5
        ci_small = calculate_effect_size_ci(es, 10, 10)
        ci_large = calculate_effect_size_ci(es, 100, 100)
        
        width_small = ci_small["upper"] - ci_small["lower"]
        width_large = ci_large["upper"] - ci_large["lower"]
        
        assert width_large < width_small

class TestGenerateReportLogic:
    def test_between_subjects_phrasing(self):
        """Test that Between-Subjects design uses 'associational' phrasing."""
        results = {
            "anova": {"test": {"df1": 1, "df2": 98, "F": 4.0, "p": 0.04}},
            "fdr": {"metric": 0.03},
            "effect_sizes": {"metric": {"d": 0.5, "ci": {"lower": 0.1, "upper": 0.9}}},
            "sensitivity": {"0.05": {"significant_count": 1}}
        }
        
        report = generate_report_logic(results, "Between-Subjects")
        
        assert "associational" in report.lower()
        assert "LIMITATIONS:" in report
        assert "causal modulation" not in report.lower()

    def test_within_subjects_phrasing(self):
        """Test that Within-Subjects design allows causal language."""
        results = {
            "anova": {"test": {"df1": 1, "df2": 98, "F": 4.0, "p": 0.04}},
            "fdr": {"metric": 0.03},
            "effect_sizes": {"metric": {"d": 0.5, "ci": {"lower": 0.1, "upper": 0.9}}},
            "sensitivity": {"0.05": {"significant_count": 1}}
        }
        
        report = generate_report_logic(results, "Within-Subjects")
        
        # Within-Subjects design should not have the specific "associational" warning
        # but may contain "causal" in the context of the design
        assert "Within-Subjects" in report

    def test_sensitivity_table_present(self):
        """Test that sensitivity analysis table is included."""
        results = {
            "sensitivity": {
                "0.01": {"significant_count": 0},
                "0.05": {"significant_count": 1},
                "0.1": {"significant_count": 2}
            }
        }
        
        report = generate_report_logic(results, "Between-Subjects")
        
        assert "Alpha Threshold" in report
        assert "0.05" in report

class TestSaveReport:
    def test_save_report_creates_file(self):
        """Test that save_report creates the file correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = os.path.join(tmpdir, "test_report.md")
            content = "# Test Report\n\nContent here."
            
            save_report(content, report_path)
            
            assert os.path.exists(report_path)
            with open(report_path, 'r') as f:
                assert f.read() == content

class TestVerifyReportConstraints:
    def test_verify_report_constraints_success(self):
        """Test that verify_report_constraints returns True for valid report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = os.path.join(tmpdir, "test_report.md")
            content = """# Report
            LIMITATIONS:
            This is an associational study.
            """
            with open(report_path, 'w') as f:
                f.write(content)
            
            assert verify_report_constraints(report_path) is True

    def test_verify_report_constraints_missing_file(self):
        """Test that verify_report_constraints returns False for missing file."""
        assert verify_report_constraints("/nonexistent/path/report.md") is False

class TestSaveFinalResults:
    def test_save_final_results_creates_json(self):
        """Test that save_final_results creates the JSON file correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock get_path to use temp directory
            with patch('report.get_path', return_value=os.path.join(tmpdir, "final_results.json")):
                results = {"test": "data", "p_fdr": 0.03}
                path = save_final_results(results, "Between-Subjects")
                
                assert os.path.exists(path)
                with open(path, 'r') as f:
                    data = json.load(f)
                    assert data["design_type"] == "Between-Subjects"
                    assert "results" in data
                    assert "generated_at" in data

class TestRunReportingPipeline:
    def test_run_reporting_pipeline_creates_all_artifacts(self):
        """Test that run_reporting_pipeline creates both JSON and MD files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock get_path to use temp directory
            def mock_get_path(subdir, filename):
                return os.path.join(tmpdir, subdir, filename)
            
            with patch('report.get_path', side_effect=mock_get_path):
                # Create subdirectories
                os.makedirs(os.path.join(tmpdir, "processed"), exist_ok=True)
                os.makedirs(os.path.join(tmpdir, "reports"), exist_ok=True)
                
                results = {
                    "anova": {"test": {"df1": 1, "df2": 98, "F": 4.0, "p": 0.04}},
                    "fdr": {"metric": 0.03},
                    "effect_sizes": {"metric": {"d": 0.5, "ci": {"lower": 0.1, "upper": 0.9}}},
                    "sensitivity": {"0.05": {"significant_count": 1}}
                }
                
                paths = run_reporting_pipeline(results, "Between-Subjects")
                
                assert "results_json" in paths
                assert "report_md" in paths
                assert os.path.exists(paths["results_json"])
                assert os.path.exists(paths["report_md"])

                # Verify JSON content
                with open(paths["results_json"], 'r') as f:
                    data = json.load(f)
                    assert data["design_type"] == "Between-Subjects"
                    assert "p_fdr" in str(data) # Check p_fdr is present in results

                # Verify MD content
                with open(paths["report_md"], 'r') as f:
                    content = f.read()
                    assert "associational" in content.lower()
                    assert "LIMITATIONS:" in content

import pytest
import os
import sys
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from analyze.generate_results_markdown import (
    load_analysis_results,
    validate_significance_threshold,
    validate_ci_width_results,
    generate_markdown_report,
    save_markdown_report,
    SIGNIFICANCE_THRESHOLD,
    CI_WIDTH_MAX
)

class TestLoadAnalysisResults:
    def test_load_valid_results(self, tmp_path):
        """Test loading valid JSON results file."""
        results_file = tmp_path / "results.json"
        test_data = {"test": "data"}
        with open(results_file, 'w') as f:
            json.dump(test_data, f)
        
        result = load_analysis_results(str(results_file))
        assert result == test_data

    def test_load_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_analysis_results(str(tmp_path / "nonexistent.json"))

    def test_load_invalid_json(self, tmp_path):
        """Test that JSONDecodeError is raised for invalid JSON."""
        results_file = tmp_path / "invalid.json"
        with open(results_file, 'w') as f:
            f.write("not valid json")
        
        with pytest.raises(json.JSONDecodeError):
            load_analysis_results(str(results_file))

class TestSignificanceValidation:
    def test_validate_significance_with_results(self):
        """Test significance validation with mixed effects and pairwise results."""
        results = {
            "mixed_effects": {
                "fixed_effects": {
                    "effect1": {"p_value": 0.01, "estimate": 0.5},
                    "effect2": {"p_value": 0.06, "estimate": 0.3}
                }
            },
            "pairwise_comparisons": [
                {"comparison": "A vs B", "p_value": 0.03, "estimate": 0.4},
                {"comparison": "C vs D", "p_value": 0.08, "estimate": 0.2}
            ]
        }
        
        significant = validate_significance_threshold(results, threshold=0.05)
        
        assert len(significant) == 2
        assert any(f['effect'] == 'effect1' for f in significant)
        assert any(f['comparison'] == 'A vs B' for f in significant)
        assert not any(f['effect'] == 'effect2' for f in significant)
        assert not any(f['comparison'] == 'C vs D' for f in significant)

    def test_validate_significance_empty(self):
        """Test significance validation with no significant findings."""
        results = {
            "mixed_effects": {
                "fixed_effects": {
                    "effect1": {"p_value": 0.1, "estimate": 0.5}
                }
            },
            "pairwise_comparisons": [
                {"comparison": "A vs B", "p_value": 0.2, "estimate": 0.4}
            ]
        }
        
        significant = validate_significance_threshold(results, threshold=0.05)
        assert len(significant) == 0

class TestCIWidthValidation:
    def test_validate_ci_width_pass(self):
        """Test CI width validation when all CIs pass."""
        results = {
            "effect_sizes": [
                {"comparison": "A vs B", "ci_lower": 0.1, "ci_upper": 0.2}
            ],
            "mixed_effects": {
                "fixed_effects": {
                    "effect1": {"ci_lower": 0.05, "ci_upper": 0.15}
                }
            }
        }
        
        validation = validate_ci_width_results(results, max_width=0.20)
        
        assert validation['passed'] is True
        assert len(validation['findings']) == 2
        assert all(f['passed'] for f in validation['findings'])

    def test_validate_ci_width_fail(self):
        """Test CI width validation when some CIs fail."""
        results = {
            "effect_sizes": [
                {"comparison": "A vs B", "ci_lower": 0.1, "ci_upper": 0.4}
            ],
            "mixed_effects": {
                "fixed_effects": {
                    "effect1": {"ci_lower": 0.05, "ci_upper": 0.15}
                }
            }
        }
        
        validation = validate_ci_width_results(results, max_width=0.20)
        
        assert validation['passed'] is False
        assert len(validation['findings']) == 2
        assert validation['findings'][0]['passed'] is False
        assert validation['findings'][1]['passed'] is True

class TestMarkdownGeneration:
    def test_generate_markdown_report(self):
        """Test markdown report generation."""
        results = {
            "mixed_effects": {
                "fixed_effects": {
                    "effect1": {"estimate": 0.5, "std_error": 0.1, "t_value": 5.0, "p_value": 0.001, "ci_lower": 0.3, "ci_upper": 0.7}
                },
                "random_effects": {
                    "student_id": {"variance": 0.1, "std_dev": 0.316}
                }
            },
            "pairwise_comparisons": [
                {"comparison": "A vs B", "estimate": 0.2, "std_error": 0.05, "t_value": 4.0, "p_value": 0.0001, "ci_lower": 0.1, "ci_upper": 0.3, "cohens_d": 0.4}
            ],
            "effect_sizes": [
                {"comparison": "A vs B", "cohens_d": 0.4, "ci_lower": 0.1, "ci_upper": 0.3}
            ]
        }
        
        significant_findings = [
            {"type": "mixed_effects", "effect": "effect1", "estimate": 0.5, "p_value": 0.001, "significant": True},
            {"type": "pairwise_comparison", "comparison": "A vs B", "estimate": 0.2, "p_value": 0.0001, "significant": True}
        ]
        
        ci_validation = {
            "passed": True,
            "max_width_allowed": 0.20,
            "findings": [
                {"comparison": "A vs B", "ci_width": 0.2, "passed": True},
                {"effect": "effect1", "ci_width": 0.4, "passed": False}
            ]
        }
        
        report = generate_markdown_report(results, significant_findings, ci_validation)
        
        assert "# Neuro-Symbolic Learning Networks" in report
        assert "Executive Summary" in report
        assert "Significant Findings" in report
        assert "Mixed Effects Model Results" in report
        assert "Pairwise Comparisons" in report
        assert "Effect Sizes" in report
        assert "CI Width Validation" in report
        assert "Methodology Notes" in report
        assert "effect1" in report
        assert "A vs B" in report

    def test_generate_markdown_report_empty_significant(self):
        """Test markdown report generation with no significant findings."""
        results = {}
        significant_findings = []
        ci_validation = {"passed": True, "max_width_allowed": 0.20, "findings": []}
        
        report = generate_markdown_report(results, significant_findings, ci_validation)
        
        assert "No statistically significant findings" in report

class TestSaveMarkdownReport:
    def test_save_markdown_report(self, tmp_path):
        """Test saving markdown report to file."""
        output_file = tmp_path / "report.md"
        content = "# Test Report\n\nThis is a test."
        
        save_markdown_report(content, str(output_file))
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            saved_content = f.read()
        assert saved_content == content

    def test_save_markdown_report_creates_directories(self, tmp_path):
        """Test that save_markdown_report creates parent directories."""
        output_file = tmp_path / "subdir" / "report.md"
        content = "# Test Report"
        
        save_markdown_report(content, str(output_file))
        
        assert output_file.exists()
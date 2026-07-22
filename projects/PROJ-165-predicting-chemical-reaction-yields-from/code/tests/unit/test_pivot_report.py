import pytest
import json
import os
import tempfile
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from scripts.generate_pivot_report import extract_code_features, verify_split_logic_usage, generate_pivot_report, TARGET_VARIABLE_CODE_PATTERNS

class TestPivotReportLogic:
    """Unit tests for the Pivot & Limitation Report generation logic."""

    def test_extract_code_features_on_nonexistent_file(self):
        """Test that extract_code_features handles missing files gracefully."""
        result = extract_code_features(Path("/nonexistent/file.py"))
        assert result["exists"] is False
        assert "error" in result

    def test_extract_code_features_on_valid_file(self, tmp_path):
        """Test that extract_code_features correctly analyzes a valid Python file."""
        # Create a test file with target variable patterns
        test_file = tmp_path / "test_target.py"
        test_content = """
        def process_energy(data):
            '''Process normalized DFT total molecular energy.'''
            normalized_energy = data * 0.5
            return normalized_energy
        """
        test_file.write_text(test_content)
        
        result = extract_code_features(test_file)
        assert result["exists"] is True
        assert result["target_pattern_count"] > 0
        assert "normalized_energy" in result["found_target_patterns"]

    def test_verify_split_logic_usage_true(self, tmp_path):
        """Test verify_split_logic_usage returns True when patterns are found."""
        test_file = tmp_path / "test_usage.py"
        test_file.write_text("normalized_dft_energy = calculate_energy()")
        
        assert verify_split_logic_usage(test_file) is True

    def test_verify_split_logic_usage_false(self, tmp_path):
        """Test verify_split_logic_usage returns False when no patterns found."""
        test_file = tmp_path / "test_no_usage.py"
        test_file.write_text("yield_percent = calculate_yield()")
        
        assert verify_split_logic_usage(test_file) is False

    def test_generate_pivot_report_structure(self):
        """Test that generate_pivot_report produces the expected structure."""
        report = generate_pivot_report()
        
        # Check top-level keys
        assert "report_title" in report
        assert "pivot_documentation" in report
        assert "limitation_documentation" in report
        assert "implementation_verification" in report
        
        # Check pivot documentation
        pivot = report["pivot_documentation"]
        assert pivot["original_target"] == "Experimental Reaction Yield"
        assert pivot["pivoted_target"] == "normalized DFT total molecular energy"
        assert "spec_plan_contradiction" in pivot
        
        # Check limitation documentation
        limitation = report["limitation_documentation"]["fr_010_limitation"]
        assert limitation["status"] == "LIMITED / CIRCULAR VALIDATION"
        assert "circular validation" in limitation["description"].lower()
        
        # Check implementation verification
        verification = report["implementation_verification"]
        assert "tasks_verified" in verification
        assert "verification_summary" in verification
        assert "total_tasks" in verification["verification_summary"]

    def test_target_variable_patterns_defined(self):
        """Test that target variable patterns are properly defined."""
        assert len(TARGET_VARIABLE_CODE_PATTERNS) > 0
        assert "normalized_energy" in TARGET_VARIABLE_CODE_PATTERNS
        assert "dft_energy" in TARGET_VARIABLE_CODE_PATTERNS

    def test_report_json_serializable(self):
        """Test that the generated report is JSON serializable."""
        report = generate_pivot_report()
        
        # This should not raise an exception
        json_str = json.dumps(report)
        assert len(json_str) > 0
        
        # Verify we can parse it back
        parsed = json.loads(json_str)
        assert parsed["report_title"] == report["report_title"]
"""
Unit tests for error analysis coverage calculation (T030b).

Tests the ErrorAnalyzer class specifically for coverage percentage calculation.
"""
import pytest
import json
import os
from pathlib import Path
from dataclasses import asdict

# Import from the project code
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from error_analysis import FailureRecord, ErrorAnalyzer, FailureCategory

class TestErrorAnalysisCoverage:
    """Tests for error analysis coverage functionality."""

    def test_coverage_calculation_empty(self):
        """Test coverage calculation with no failures."""
        analyzer = ErrorAnalyzer()
        coverage = analyzer.calculate_coverage()
        assert coverage == 0.0

    def test_coverage_calculation_all_categorized(self):
        """Test coverage when all failures are categorized."""
        analyzer = ErrorAnalyzer()
        
        # Add categorized failures
        for i in range(5):
            record = FailureRecord(
                trace_id=f"trace_{i}",
                error_type="discretization_error",
                category="discretization_ambiguity",
                categorized=True
            )
            analyzer.add_failure(record)
        
        coverage = analyzer.calculate_coverage()
        assert coverage == 100.0

    def test_coverage_calculation_partial(self):
        """Test coverage when only some failures are categorized."""
        analyzer = ErrorAnalyzer()
        
        # Add 3 categorized, 2 uncategorized
        for i in range(3):
            record = FailureRecord(
                trace_id=f"cat_{i}",
                error_type="logic_error",
                category="logical_inference_limitations",
                categorized=True
            )
            analyzer.add_failure(record)
        
        for i in range(2):
            record = FailureRecord(
                trace_id=f"uncat_{i}",
                error_type="unknown_error",
                category=None,
                categorized=False
            )
            analyzer.add_failure(record)
        
        coverage = analyzer.calculate_coverage()
        # 3 out of 5 = 60%
        assert coverage == 60.0

    def test_coverage_calculation_none_categorized(self):
        """Test coverage when no failures are categorized."""
        analyzer = ErrorAnalyzer()
        
        for i in range(5):
            record = FailureRecord(
                trace_id=f"trace_{i}",
                error_type="unknown",
                categorized=False
            )
            analyzer.add_failure(record)
        
        coverage = analyzer.calculate_coverage()
        assert coverage == 0.0

    def test_report_generation(self):
        """Test that the report contains correct coverage data."""
        analyzer = ErrorAnalyzer()
        
        # Add 4 categorized, 1 uncategorized
        for i in range(4):
            record = FailureRecord(
                trace_id=f"cat_{i}",
                error_type="discretization",
                categorized=True
            )
            analyzer.add_failure(record)
        
        record_uncat = FailureRecord(
            trace_id="uncat_1",
            error_type="unknown",
            categorized=False
        )
        analyzer.add_failure(record_uncat)
        
        report = analyzer.generate_report()
        
        assert report.total_failures == 5
        assert report.categorized_failures == 4
        assert report.uncategorized_failures == 1
        assert report.coverage_percentage == 80.0
        assert len(report.uncategorized_samples) == 1

    def test_categorization_updates_coverage(self):
        """Test that categorizing a failure updates the coverage."""
        analyzer = ErrorAnalyzer()
        
        # Add uncategorized failure
        record = FailureRecord(
            trace_id="test_1",
            error_type="ambiguous_token",
            categorized=False
        )
        analyzer.add_failure(record)
        
        assert analyzer.calculate_coverage() == 0.0
        
        # Categorize it
        analyzer.categorize_failure(record)
        
        assert record.categorized is True
        assert analyzer.calculate_coverage() == 100.0

    def test_main_function_creates_output(self, tmp_path):
        """Test that main() creates the expected output file."""
        # Setup temp directories
        data_results = tmp_path / "data" / "results"
        data_results.mkdir(parents=True)
        
        # Create a mock failures.json
        failures_data = [
            {"trace_id": "1", "error_type": "ambiguous", "categorized": True},
            {"trace_id": "2", "error_type": "logic", "categorized": True},
            {"trace_id": "3", "error_type": "unknown", "categorized": False}
        ]
        failures_file = data_results / "failures.json"
        with open(failures_file, "w") as f:
            json.dump(failures_data, f)
        
        # Change working directory to tmp_path to simulate project root
        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Run main
            from error_analysis import main
            main()
            
            # Check output
            output_file = data_results / "error_coverage.json"
            assert output_file.exists()
            
            with open(output_file, "r") as f:
                report = json.load(f)
            
            assert report["total_failures"] == 3
            assert report["categorized_failures"] == 2
            assert report["coverage_percentage"] == 66.66666666666666
        finally:
            os.chdir(original_cwd)
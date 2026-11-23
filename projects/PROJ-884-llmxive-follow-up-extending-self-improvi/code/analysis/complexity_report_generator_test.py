"""
Unit tests for the complexity report generator.

This module tests the functionality of code/analysis/complexity_report_generator.py
to ensure it correctly generates the complexity report.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.complexity_report_generator import (
    load_json_file,
    generate_complexity_report,
    save_report,
    PROJECT_ROOT,
    DATA_PROCESSED_DIR,
    COMPLEXITY_RECONCILE_FILE,
    COMPLEXITY_REPORT_FILE
)

class TestLoadJsonFile:
    """Tests for the load_json_file function."""
    
    def test_load_valid_json(self, tmp_path):
        """Test loading a valid JSON file."""
        test_data = {"key": "value", "number": 42}
        test_file = tmp_path / "test.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        result = load_json_file(test_file)
        assert result == test_data
    
    def test_load_nonexistent_file(self, tmp_path):
        """Test loading a non-existent file returns None."""
        nonexistent_file = tmp_path / "nonexistent.json"
        result = load_json_file(nonexistent_file)
        assert result is None
    
    def test_load_invalid_json(self, tmp_path):
        """Test loading an invalid JSON file returns None."""
        test_file = tmp_path / "invalid.json"
        with open(test_file, 'w') as f:
            f.write("{invalid json}")
        
        result = load_json_file(test_file)
        assert result is None

class TestGenerateComplexityReport:
    """Tests for the generate_complexity_report function."""
    
    def test_generate_complete_report(self):
        """Test generating a report from complete reconcile data."""
        reconcile_data = {
            "reconciled_complexity_class": "O(n log n)",
            "empirical_complexity_class": "O(n log n)",
            "theoretical_complexity_class": "O(n log n)",
            "reconciliation_method": "empirical_preferred",
            "discrepancy_detected": False,
            "notes": ["All methods agree"]
        }
        
        report = generate_complexity_report(reconcile_data)
        
        assert report["reconciled_complexity_class"] == "O(n log n)"
        assert report["empirical_complexity_class"] == "O(n log n)"
        assert report["theoretical_complexity_class"] == "O(n log n)"
        assert report["reconciliation_method"] == "empirical_preferred"
        assert report["discrepancy_detected"] is False
        assert "All methods agree" in report["notes"]
    
    def test_generate_report_with_missing_fields(self):
        """Test generating a report from incomplete reconcile data."""
        reconcile_data = {
            "reconciled_complexity_class": "O(n log n)",
            "discrepancy_detected": True
        }
        
        report = generate_complexity_report(reconcile_data)
        
        assert report["reconciled_complexity_class"] == "O(n log n)"
        assert report["empirical_complexity_class"] is None
        assert report["theoretical_complexity_class"] is None
        assert report["reconciliation_method"] is None
        assert report["discrepancy_detected"] is True
        assert len([n for n in report["notes"] if "Missing" in n]) == 3
    
    def test_generate_report_with_discrepancy(self):
        """Test generating a report when discrepancy is detected."""
        reconcile_data = {
            "reconciled_complexity_class": "O(n log n)",
            "empirical_complexity_class": "O(n^2)",
            "theoretical_complexity_class": "O(n log n)",
            "reconciliation_method": "theoretical_preferred",
            "discrepancy_detected": True,
            "notes": ["Empirical and theoretical disagree"]
        }
        
        report = generate_complexity_report(reconcile_data)
        
        assert report["reconciled_complexity_class"] == "O(n log n)"
        assert report["empirical_complexity_class"] == "O(n^2)"
        assert report["theoretical_complexity_class"] == "O(n log n)"
        assert report["discrepancy_detected"] is True
        assert "Discrepancy detected between empirical and theoretical results" in report["notes"]

class TestSaveReport:
    """Tests for the save_report function."""
    
    def test_save_report_success(self, tmp_path):
        """Test saving a report successfully."""
        report = {
            "reconciled_complexity_class": "O(n log n)",
            "empirical_complexity_class": "O(n log n)",
            "theoretical_complexity_class": "O(n log n)",
            "reconciliation_method": "empirical_preferred",
            "discrepancy_detected": False,
            "notes": []
        }
        
        output_file = tmp_path / "complexity_report.json"
        success = save_report(report, output_file)
        
        assert success is True
        assert output_file.exists()
        
        # Verify the content
        with open(output_file, 'r') as f:
            saved_report = json.load(f)
        
        assert saved_report == report
    
    def test_save_report_creates_directories(self, tmp_path):
        """Test that save_report creates necessary directories."""
        report = {"test": "data"}
        nested_path = tmp_path / "nested" / "path" / "report.json"
        
        success = save_report(report, nested_path)
        
        assert success is True
        assert nested_path.exists()

class TestIntegration:
    """Integration tests for the complexity report generation workflow."""
    
    def test_full_workflow(self, tmp_path):
        """Test the full workflow from reconcile data to report."""
        # Create a temporary reconcile data file
        reconcile_data = {
            "reconciled_complexity_class": "O(n log n)",
            "empirical_complexity_class": "O(n log n)",
            "theoretical_complexity_class": "O(n log n)",
            "reconciliation_method": "empirical_preferred",
            "discrepancy_detected": False,
            "notes": ["Test integration"]
        }
        
        reconcile_file = tmp_path / "complexity_reconcile_status.json"
        with open(reconcile_file, 'w') as f:
            json.dump(reconcile_data, f)
        
        # Create a temporary output path
        output_file = tmp_path / "complexity_report.json"
        
        # Load and process
        loaded_data = load_json_file(reconcile_file)
        assert loaded_data is not None
        
        report = generate_complexity_report(loaded_data)
        success = save_report(report, output_file)
        
        assert success is True
        assert output_file.exists()
        
        # Verify the output
        with open(output_file, 'r') as f:
            final_report = json.load(f)
        
        assert final_report["reconciled_complexity_class"] == "O(n log n)"
        assert final_report["discrepancy_detected"] is False
        assert "Test integration" in final_report["notes"]
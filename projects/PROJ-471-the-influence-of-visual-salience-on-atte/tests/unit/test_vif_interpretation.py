import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the code directory to the path for imports
code_path = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_path))

from analysis.vif_interpretation import (
    load_vif_verification_report,
    interpret_vif_results,
    write_vif_report
)

class TestVIFInterpretation:
    """
    Unit tests for T030a: VIF Interpretation logic.
    """

    def test_load_vif_verification_report_success(self, tmp_path):
        """Test successful loading of a valid VIF report."""
        report_data = {
            "vif_scores": {
                "salience": 6.5,
                "luminance": 2.1,
                "contrast": 3.4
            },
            "threshold": 5.0,
            "status": "calculated"
        }
        
        report_file = tmp_path / "vif_verification.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f)
        
        result = load_vif_verification_report(report_file)
        
        assert result is not None
        assert result["vif_scores"]["salience"] == 6.5
        assert result["threshold"] == 5.0

    def test_load_vif_verification_report_file_not_found(self, tmp_path):
        """Test handling of missing report file."""
        non_existent_path = tmp_path / "non_existent.json"
        result = load_vif_verification_report(non_existent_path)
        
        assert result is None

    def test_load_vif_verification_report_invalid_json(self, tmp_path):
        """Test handling of invalid JSON file."""
        report_file = tmp_path / "invalid.json"
        report_file.write_text("not valid json {")
        
        result = load_vif_verification_report(report_file)
        
        assert result is None

    def test_interpret_vif_results_high_vif(self):
        """Test interpretation when VIF > threshold (multicollinearity detected)."""
        vif_data = {
            "vif_scores": {
                "salience": 8.5,
                "luminance": 2.1
            }
        }
        
        report = interpret_vif_results(vif_data, threshold=5.0)
        
        assert "MULTICOLLINEARITY DETECTED" in report
        assert "VIF > 5" in report
        assert "SCR-002" in report
        assert "EXCLUDED" in report
        assert "8.5" in report

    def test_interpret_vif_results_low_vif(self):
        """Test interpretation when VIF <= threshold."""
        vif_data = {
            "vif_scores": {
                "salience": 3.2,
                "luminance": 1.5
            }
        }
        
        report = interpret_vif_results(vif_data, threshold=5.0)
        
        assert "No severe multicollinearity" in report
        assert "VIF <= 5" in report
        assert "SCR-002" in report
        assert "remains excluded" in report

    def test_interpret_vif_results_missing_salience(self):
        """Test handling when salience VIF is missing."""
        vif_data = {
            "vif_scores": {
                "luminance": 2.1
            }
        }
        
        report = interpret_vif_results(vif_data, threshold=5.0)
        
        assert "ERROR" in report
        assert "Salience VIF score not found" in report

    def test_write_vif_report_success(self, tmp_path):
        """Test successful writing of the report file."""
        content = "Test report content\nLine 2"
        output_file = tmp_path / "test_report.txt"
        
        success = write_vif_report(content, output_file)
        
        assert success is True
        assert output_file.exists()
        assert output_file.read_text() == content

    def test_write_vif_report_creates_directories(self, tmp_path):
        """Test that write_vif_report creates parent directories if needed."""
        content = "Test content"
        output_file = tmp_path / "subdir1" / "subdir2" / "report.txt"
        
        success = write_vif_report(content, output_file)
        
        assert success is True
        assert output_file.exists()
        assert output_file.read_text() == content

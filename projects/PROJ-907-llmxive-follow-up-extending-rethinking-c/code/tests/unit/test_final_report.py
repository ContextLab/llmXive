import json
import pytest
import tempfile
from pathlib import Path
import sys
import os

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.final_report import (
    load_json_file,
    extract_sensitivity_range,
    generate_final_report
)

class TestFinalReport:
    """Tests for the final report generation functionality."""

    def test_load_json_file_valid(self, tmp_path):
        """Test loading a valid JSON file."""
        test_data = {"key": "value", "number": 42}
        json_file = tmp_path / "test.json"
        
        with open(json_file, 'w') as f:
            json.dump(test_data, f)
        
        result = load_json_file(str(json_file))
        assert result == test_data

    def test_load_json_file_not_found(self, tmp_path):
        """Test loading a non-existent JSON file."""
        result = load_json_file(str(tmp_path / "nonexistent.json"))
        assert result is None

    def test_load_json_file_invalid_json(self, tmp_path):
        """Test loading a file with invalid JSON."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text("not valid json {")
        
        result = load_json_file(str(json_file))
        assert result is None

    def test_extract_sensitivity_range_valid(self):
        """Test extracting sensitivity range from valid data."""
        sensitivity_data = {
            "results": [
                {"threshold": 0.01, "fid_score": 10.5},
                {"threshold": 0.05, "fid_score": 12.3},
                {"threshold": 0.1, "fid_score": 11.8}
            ]
        }
        
        result = extract_sensitivity_range(sensitivity_data)
        
        assert result["min"] == 10.5
        assert result["max"] == 12.3
        assert result["range"] == 1.8

    def test_extract_sensitivity_range_empty(self):
        """Test extracting sensitivity range from empty data."""
        sensitivity_data = {"results": []}
        result = extract_sensitivity_range(sensitivity_data)
        
        assert result["min"] == 0.0
        assert result["max"] == 0.0
        assert result["range"] == 0.0

    def test_extract_sensitivity_range_missing_key(self):
        """Test extracting sensitivity range when 'results' key is missing."""
        sensitivity_data = {"other_key": "value"}
        result = extract_sensitivity_range(sensitivity_data)
        
        assert result["min"] == 0.0
        assert result["max"] == 0.0
        assert result["range"] == 0.0

    def test_generate_final_report(self, tmp_path):
        """Test generating the final report."""
        statistical_data = {
            "mean": 0.05,
            "std": 0.02,
            "bootstrap_results": {
                "p_value": 0.03,
                "ci_lower": 0.01,
                "ci_upper": 0.09
            },
            "statistical_limitations": "N=5 is small for parametric tests"
        }
        
        sensitivity_data = {
            "results": [
                {"threshold": 0.01, "fid_score": 10.5},
                {"threshold": 0.05, "fid_score": 12.3},
                {"threshold": 0.1, "fid_score": 11.8}
            ]
        }
        
        output_file = tmp_path / "final_report.json"
        
        success = generate_final_report(
            statistical_data=statistical_data,
            sensitivity_data=sensitivity_data,
            output_path=str(output_file)
        )
        
        assert success
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            report = json.load(f)
        
        # Verify structure
        assert "statistical_analysis" in report
        assert "sensitivity_analysis" in report
        assert "summary" in report
        
        # Verify statistical analysis
        assert report["statistical_analysis"]["mean_fid_difference"] == 0.05
        assert report["statistical_analysis"]["std_fid_difference"] == 0.02
        assert report["statistical_analysis"]["bootstrap_results"]["p_value"] == 0.03
        
        # Verify sensitivity analysis
        assert report["sensitivity_analysis"]["fid_degradation_range"]["min"] == 10.5
        assert report["sensitivity_analysis"]["fid_degradation_range"]["max"] == 12.3
        assert report["sensitivity_analysis"]["fid_degradation_range"]["range"] == 1.8

    def test_generate_final_report_missing_statistical_data(self, tmp_path):
        """Test generating report with missing statistical data."""
        sensitivity_data = {
            "results": [
                {"threshold": 0.01, "fid_score": 10.5}
            ]
        }
        
        output_file = tmp_path / "final_report.json"
        
        success = generate_final_report(
            statistical_data=None,
            sensitivity_data=sensitivity_data,
            output_path=str(output_file)
        )
        
        assert success
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            report = json.load(f)
        
        # Verify defaults are used
        assert report["statistical_analysis"]["mean_fid_difference"] == 0.0
        assert report["statistical_analysis"]["std_fid_difference"] == 0.0

    def test_generate_final_report_missing_sensitivity_data(self, tmp_path):
        """Test generating report with missing sensitivity data."""
        statistical_data = {
            "mean": 0.05,
            "std": 0.02,
            "bootstrap_results": {
                "p_value": 0.03,
                "ci_lower": 0.01,
                "ci_upper": 0.09
            },
            "statistical_limitations": "Limitation note"
        }
        
        output_file = tmp_path / "final_report.json"
        
        success = generate_final_report(
            statistical_data=statistical_data,
            sensitivity_data=None,
            output_path=str(output_file)
        )
        
        assert success
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            report = json.load(f)
        
        # Verify sensitivity range defaults
        assert report["sensitivity_analysis"]["fid_degradation_range"]["min"] == 0.0
        assert report["sensitivity_analysis"]["fid_degradation_range"]["range"] == 0.0

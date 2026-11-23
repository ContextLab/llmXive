import json
import pytest
import tempfile
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.final_report import load_json_file, extract_sensitivity_range, generate_final_report

class TestFinalReport:
    
    def test_load_json_file_valid(self, tmp_path):
        """Test loading a valid JSON file."""
        test_data = {"key": "value", "number": 42}
        test_file = tmp_path / "test.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        result = load_json_file(str(test_file))
        assert result == test_data
    
    def test_load_json_file_not_found(self, tmp_path):
        """Test loading a non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_json_file(str(tmp_path / "nonexistent.json"))
    
    def test_load_json_file_invalid_json(self, tmp_path):
        """Test loading a file with invalid JSON raises error."""
        test_file = tmp_path / "invalid.json"
        with open(test_file, 'w') as f:
            f.write("not valid json {")
        
        with pytest.raises(json.JSONDecodeError):
            load_json_file(str(test_file))
    
    def test_extract_sensitivity_range_valid(self):
        """Test extracting range from valid sensitivity data."""
        sensitivity_data = [
            {"threshold": 0.01, "fid_score": 10.5},
            {"threshold": 0.05, "fid_score": 12.3},
            {"threshold": 0.1, "fid_score": 11.8}
        ]
        
        result = extract_sensitivity_range(sensitivity_data)
        
        assert result["min"] == 10.5
        assert result["max"] == 12.3
        assert abs(result["range"] - 1.8) < 0.001
    
    def test_extract_sensitivity_range_empty(self):
        """Test extracting range from empty data."""
        result = extract_sensitivity_range([])
        assert result["min"] == 0.0
        assert result["max"] == 0.0
        assert result["range"] == 0.0
    
    def test_extract_sensitivity_range_missing_fid(self):
        """Test extracting range when fid_score is missing."""
        sensitivity_data = [
            {"threshold": 0.01},
            {"threshold": 0.05, "fid_score": 12.3}
        ]
        
        result = extract_sensitivity_range(sensitivity_data)
        assert result["min"] == 12.3
        assert result["max"] == 12.3
        assert result["range"] == 0.0
    
    def test_generate_final_report(self, tmp_path):
        """Test generating a complete final report."""
        stats_data = {
            "mean": 0.05,
            "std": 0.02,
            "paired_differences": [0.04, 0.06, 0.05],
            "bootstrap_results": {"p_value": 0.03},
            "statistical_limitations": "N=5"
        }
        
        sensitivity_data = {
            "thresholds": [0.01, 0.05, 0.1],
            "results": [
                {"threshold": 0.01, "fid_score": 10.0},
                {"threshold": 0.05, "fid_score": 10.5},
                {"threshold": 0.1, "fid_score": 11.0}
            ],
            "robustness_conclusion": "Robust",
            "rationale": "Covered low to high"
        }
        
        output_file = tmp_path / "final_report.json"
        
        report = generate_final_report(stats_data, sensitivity_data, str(output_file))
        
        # Verify file was created
        assert output_file.exists()
        
        # Verify content
        with open(output_file, 'r') as f:
            saved_report = json.load(f)
        
        assert saved_report["statistical_analysis"]["mean"] == 0.05
        assert saved_report["statistical_analysis"]["std"] == 0.02
        assert saved_report["sensitivity_analysis"]["fid_range"]["min"] == 10.0
        assert saved_report["sensitivity_analysis"]["fid_range"]["max"] == 11.0
        assert abs(saved_report["sensitivity_analysis"]["fid_range"]["range"] - 1.0) < 0.001
        assert saved_report["summary"]["sensitivity_range"] == 1.0
    
    def test_generate_final_report_missing_stats(self, tmp_path):
        """Test generating report with missing statistical data."""
        stats_data = {}
        sensitivity_data = {
            "results": [{"fid_score": 10.0}]
        }
        
        output_file = tmp_path / "final_report.json"
        report = generate_final_report(stats_data, sensitivity_data, str(output_file))
        
        assert report["statistical_analysis"]["mean"] == 0.0
        assert report["statistical_analysis"]["std"] == 0.0
        assert report["sensitivity_analysis"]["fid_range"]["min"] == 10.0
    
    def test_generate_final_report_missing_sensitivity(self, tmp_path):
        """Test generating report with missing sensitivity data."""
        stats_data = {"mean": 0.05}
        sensitivity_data = {}
        
        output_file = tmp_path / "final_report.json"
        report = generate_final_report(stats_data, sensitivity_data, str(output_file))
        
        assert report["sensitivity_analysis"]["fid_range"]["min"] == 0.0
        assert report["sensitivity_analysis"]["fid_range"]["max"] == 0.0
        assert report["sensitivity_analysis"]["fid_range"]["range"] == 0.0
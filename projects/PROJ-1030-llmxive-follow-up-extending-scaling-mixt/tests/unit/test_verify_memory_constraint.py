import json
import tempfile
from pathlib import Path
import pytest
import sys
import os

# Add the code directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.verify_memory_constraint import (
    load_memory_log,
    analyze_memory_usage,
    generate_verification_report,
    MAX_RAM_MB
)


class TestLoadMemoryLog:
    def test_load_valid_log_list(self, tmp_path):
        """Test loading a valid memory log with list structure."""
        log_file = tmp_path / "memory_log.json"
        test_data = [
            {"memory_mb": 1024, "timestamp": "2023-01-01T00:00:00"},
            {"memory_mb": 2048, "timestamp": "2023-01-01T00:01:00"}
        ]
        with open(log_file, 'w') as f:
            json.dump(test_data, f)
        
        entries = load_memory_log(log_file)
        assert len(entries) == 2
        assert entries[0]["memory_mb"] == 1024
    
    def test_load_valid_log_dict_entries(self, tmp_path):
        """Test loading a valid memory log with dict containing 'entries' key."""
        log_file = tmp_path / "memory_log.json"
        test_data = {
            "entries": [
                {"peak_memory_mb": 3000, "timestamp": "2023-01-01T00:00:00"},
                {"peak_memory_mb": 4000, "timestamp": "2023-01-01T00:01:00"}
            ]
        }
        with open(log_file, 'w') as f:
            json.dump(test_data, f)
        
        entries = load_memory_log(log_file)
        assert len(entries) == 2
        assert entries[0]["peak_memory_mb"] == 3000
    
    def test_load_nonexistent_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        log_file = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            load_memory_log(log_file)
    
    def test_load_invalid_json(self, tmp_path):
        """Test that JSONDecodeError is raised for invalid JSON."""
        log_file = tmp_path / "invalid.json"
        with open(log_file, 'w') as f:
            f.write("{ invalid json }")
        
        with pytest.raises(json.JSONDecodeError):
            load_memory_log(log_file)


class TestAnalyzeMemoryUsage:
    def test_analyze_normal_usage(self):
        """Test analysis of normal memory usage entries."""
        entries = [
            {"memory_mb": 1000},
            {"memory_mb": 2000},
            {"memory_mb": 3000}
        ]
        peak, avg, high = analyze_memory_usage(entries)
        
        assert peak == 3000.0
        assert avg == 2000.0
        assert len(high) == 0  # None exceed 90% of 7GB (7168 MB)
    
    def test_analyze_high_usage(self):
        """Test analysis with entries exceeding 90% threshold."""
        threshold_90 = MAX_RAM_MB * 0.9
        entries = [
            {"memory_mb": 1000},
            {"memory_mb": threshold_90 + 100},  # Exceeds 90%
            {"memory_mb": 3000}
        ]
        peak, avg, high = analyze_memory_usage(entries)
        
        assert peak == threshold_90 + 100.0
        assert len(high) == 1
        assert high[0]["memory_mb"] == threshold_90 + 100.0
    
    def test_analyze_empty_entries(self):
        """Test analysis with empty entries list."""
        entries = []
        peak, avg, high = analyze_memory_usage(entries)
        
        assert peak == 0.0
        assert avg == 0.0
        assert len(high) == 0
    
    def test_analyze_mixed_keys(self):
        """Test analysis with different memory key names."""
        entries = [
            {"memory_mb": 1000},
            {"peak_memory_mb": 2000},
            {"usage_mb": 3000}
        ]
        peak, avg, high = analyze_memory_usage(entries)
        
        assert peak == 3000.0
        assert avg == 2000.0


class TestGenerateVerificationReport:
    def test_report_pass(self, tmp_path):
        """Test generating a passing verification report."""
        entries = [{"memory_mb": 4000}]
        peak, avg, high = analyze_memory_usage(entries)
        
        log_path = tmp_path / "log.json"
        output_path = tmp_path / "verification.json"
        
        report = generate_verification_report(peak, avg, high, log_path, output_path)
        
        assert report["status"] == "pass"
        assert report["peak_memory_mb"] == 4000.0
        assert "is within" in report["message"]
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            saved_report = json.load(f)
        assert saved_report["status"] == "pass"
    
    def test_report_fail(self, tmp_path):
        """Test generating a failing verification report."""
        # Create entries that exceed the limit
        entries = [{"memory_mb": MAX_RAM_MB + 1000}]
        peak, avg, high = analyze_memory_usage(entries)
        
        log_path = tmp_path / "log.json"
        output_path = tmp_path / "verification.json"
        
        report = generate_verification_report(peak, avg, high, log_path, output_path)
        
        assert report["status"] == "fail"
        assert "exceeds" in report["message"]
        assert output_path.exists()
    
    def test_creates_output_directory(self, tmp_path):
        """Test that the function creates the output directory if it doesn't exist."""
        entries = [{"memory_mb": 1000}]
        peak, avg, high = analyze_memory_usage(entries)
        
        log_path = tmp_path / "log.json"
        output_path = tmp_path / "subdir" / "verification.json"
        
        generate_verification_report(peak, avg, high, log_path, output_path)
        
        assert output_path.exists()
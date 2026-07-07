"""
Unit tests for stats.py module (T014).

Tests per-sample vulnerability counting logic.
"""
import json
import os
import tempfile
from pathlib import Path
import pandas as pd
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from stats import (
    extract_task_id_from_path,
    extract_source_type,
    count_lines_of_code,
    parse_vulnerability_report,
    calculate_per_sample_stats
)


class TestExtractTaskId:
    """Test task ID extraction from file paths."""
    
    def test_llm_generated_path(self):
        """Test extracting task_id from LLM generated path."""
        path = "data/generated/starcoder/human_eval/test_0/samples/sample_1.py"
        assert extract_task_id_from_path(path) == "test_0"
    
    def test_human_path(self):
        """Test extracting task_id from human written path."""
        path = "data/human/human_eval/test_0/solution.py"
        assert extract_task_id_from_path(path) == "test_0"
    
    def test_mbpp_path(self):
        """Test extracting task_id from MBPP path."""
        path = "data/generated/codegen/mbpp/task_5/samples/sol_2.py"
        assert extract_task_id_from_path(path) == "task_5"
    
    def test_invalid_path(self):
        """Test with path that doesn't contain task_id."""
        path = "data/processed/report.json"
        result = extract_task_id_from_path(path)
        assert result is None


class TestExtractSourceType:
    """Test source type extraction."""
    
    def test_llm_source(self):
        """Test LLM source detection."""
        path = "data/generated/starcoder/human_eval/test_0/samples/sample.py"
        assert extract_source_type(path) == "LLM"
    
    def test_human_source(self):
        """Test Human source detection."""
        path = "data/human/human_eval/test_0/solution.py"
        assert extract_source_type(path) == "Human"
    
    def test_unknown_source(self):
        """Test unknown source detection."""
        path = "data/other/file.py"
        assert extract_source_type(path) == "Unknown"


class TestCountLinesOfCode:
    """Test LOC counting."""
    
    def test_simple_file(self, tmp_path):
        """Test counting lines in a simple file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello():\n    print('hi')\n")
        
        loc = count_lines_of_code(str(test_file))
        assert loc == 2
    
    def test_file_with_comments(self, tmp_path):
        """Test that comment-only lines are excluded."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# comment\n\ndef hello():\n    pass\n")
        
        loc = count_lines_of_code(str(test_file))
        assert loc == 2  # Only 'def hello()' and 'pass'
    
    def test_empty_file(self, tmp_path):
        """Test handling of empty file."""
        test_file = tmp_path / "empty.py"
        test_file.write_text("")
        
        loc = count_lines_of_code(str(test_file))
        assert loc == 1  # Minimum 1 line if file exists
    
    def test_nonexistent_file(self):
        """Test handling of nonexistent file."""
        loc = count_lines_of_code("/nonexistent/path/file.py")
        assert loc == 1  # Should return 1 with warning


class TestParseVulnerabilityReport:
    """Test vulnerability report parsing."""
    
    def test_parse_single_vulnerability(self, tmp_path):
        """Test parsing a report with one vulnerability."""
        report_file = tmp_path / "report.json"
        data = [
            {
                "file_path": "data/generated/test.py",
                "cwe_id": "CWE-78",
                "severity": "HIGH",
                "line_number": 10
            }
        ]
        report_file.write_text(json.dumps(data))
        
        result = parse_vulnerability_report(str(report_file))
        assert len(result) == 1
        assert "data/generated/test.py" in result
        assert len(result["data/generated/test.py"]) == 1
    
    def test_parse_multiple_files(self, tmp_path):
        """Test parsing report with vulnerabilities in multiple files."""
        report_file = tmp_path / "report.json"
        data = [
            {"file_path": "file1.py", "cwe_id": "CWE-78", "severity": "HIGH", "line_number": 1},
            {"file_path": "file2.py", "cwe_id": "CWE-89", "severity": "MEDIUM", "line_number": 5},
            {"file_path": "file1.py", "cwe_id": "CWE-123", "severity": "LOW", "line_number": 10}
        ]
        report_file.write_text(json.dumps(data))
        
        result = parse_vulnerability_report(str(report_file))
        assert len(result) == 2
        assert len(result["file1.py"]) == 2
        assert len(result["file2.py"]) == 1
    
    def test_empty_report(self, tmp_path):
        """Test parsing an empty report."""
        report_file = tmp_path / "report.json"
        report_file.write_text("[]")
        
        result = parse_vulnerability_report(str(report_file))
        assert result == {}


class TestCalculatePerSampleStats:
    """Test the main T014 functionality."""
    
    def test_full_pipeline(self, tmp_path):
        """Test the complete per-sample stats calculation."""
        # Create mock vulnerability report
        report_file = tmp_path / "vulnerability_reports.json"
        data = [
            {
                "file_path": "data/generated/starcoder/human_eval/test_0/samples/s1.py",
                "cwe_id": "CWE-78",
                "severity": "HIGH",
                "line_number": 10
            },
            {
                "file_path": "data/generated/starcoder/human_eval/test_0/samples/s1.py",
                "cwe_id": "CWE-89",
                "severity": "MEDIUM",
                "line_number": 15
            },
            {
                "file_path": "data/generated/starcoder/human_eval/test_1/samples/s1.py",
                "cwe_id": "CWE-123",
                "severity": "LOW",
                "line_number": 5
            },
            {
                "file_path": "data/human/human_eval/test_0/solution.py",
                "cwe_id": "CWE-78",
                "severity": "HIGH",
                "line_number": 20
            }
        ]
        report_file.write_text(json.dumps(data))
        
        # Create the corresponding code files
        for item in data:
            file_path = Path(item["file_path"])
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("# Test code\nprint('hello')\n")
        
        output_file = tmp_path / "raw_vulnerability_counts.csv"
        
        # Run the function
        df = calculate_per_sample_stats(str(report_file), str(output_file))
        
        # Verify output
        assert os.path.exists(output_file)
        assert len(df) == 3  # 3 unique files
        
        # Check schema
        expected_cols = ['task_id', 'source_type', 'file_path', 'lines_of_code', 'vulnerability_count']
        assert list(df.columns) == expected_cols
        
        # Check specific values
        s1_test0 = df[df['file_path'].str.contains('test_0/samples/s1.py')]
        assert len(s1_test0) == 1
        assert s1_test0.iloc[0]['vulnerability_count'] == 2
        assert s1_test0.iloc[0]['source_type'] == 'LLM'
        
        human_test0 = df[df['file_path'].str.contains('human_eval/test_0/solution.py')]
        assert len(human_test0) == 1
        assert human_test0.iloc[0]['vulnerability_count'] == 1
        assert human_test0.iloc[0]['source_type'] == 'Human'
    
    def test_empty_report(self, tmp_path):
        """Test with empty vulnerability report."""
        report_file = tmp_path / "vulnerability_reports.json"
        report_file.write_text("[]")
        
        output_file = tmp_path / "raw_vulnerability_counts.csv"
        
        df = calculate_per_sample_stats(str(report_file), str(output_file))
        
        assert os.path.exists(output_file)
        assert len(df) == 0
        assert list(df.columns) == ['task_id', 'source_type', 'file_path', 
                                   'lines_of_code', 'vulnerability_count']
    
    def test_missing_input_file(self, tmp_path):
        """Test with missing input file."""
        output_file = tmp_path / "output.csv"
        
        with pytest.raises(FileNotFoundError):
            calculate_per_sample_stats("/nonexistent/report.json", str(output_file))
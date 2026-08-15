import json
import os
import tempfile
import pytest
from pathlib import Path

# Import the functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))
from research.validate_citation_log import (
    load_json_file,
    parse_validation_report,
    write_citation_log
)

class TestParseValidationReport:
    def test_parse_all_valid(self):
        report_data = [
            {
                "title": "Lee & See (2004)",
                "doi": "10.1518/001872004772975261",
                "overlap_score": 0.85,
                "status": "valid"
            },
            {
                "title": "Langer (1975)",
                "doi": "10.1037/0022-3514.32.2.311",
                "overlap_score": 0.92,
                "status": "valid"
            }
        ]
        
        log_content = parse_validation_report(report_data)
        
        assert "Citation Verification Log" in log_content
        assert "Status: valid" in log_content
        assert "Lee & See (2004)" in log_content
        assert "Langer (1975)" in log_content
        assert "001872004772975261" in log_content
        assert "0022-3514.32.2.311" in log_content
    
    def test_parse_with_invalid(self):
        report_data = [
            {
                "title": "Valid Citation",
                "doi": "10.1234/valid",
                "overlap_score": 0.85,
                "status": "valid"
            },
            {
                "title": "Invalid Citation",
                "doi": "10.1234/invalid",
                "overlap_score": 0.45,
                "status": "invalid"
            }
        ]
        
        log_content = parse_validation_report(report_data)
        
        assert "Status: invalid" in log_content
        assert "Some citations failed verification" in log_content

class TestWriteCitationLog:
    def test_write_citation_log(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_log.md")
            log_content = "# Test Log\n\nStatus: valid"
            
            write_citation_log(log_content, output_path)
            
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                content = f.read()
            
            assert content == log_content
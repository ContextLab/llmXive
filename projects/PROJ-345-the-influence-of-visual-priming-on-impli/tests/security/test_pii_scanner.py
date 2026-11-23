import pytest
import json
import os
from pathlib import Path
from code.security.pii_scanner import (
    scan_text_for_pii,
    scan_csv_file,
    scan_json_file,
    scan_directory_for_pii,
    generate_security_report,
    run_pii_security_check
)
from code.config import Config

class TestPIIScanner:
    def test_scan_text_email(self):
        text = "Contact us at test@example.com for support."
        results = scan_text_for_pii(text)
        assert len(results) == 1
        assert results[0].pattern_type == 'email'
        assert 'test@example.com' in results[0].matched_text

    def test_scan_text_ssn(self):
        text = "SSN: 123-45-6789"
        results = scan_text_for_pii(text)
        assert len(results) == 1
        assert results[0].pattern_type == 'ssn'

    def test_scan_text_phone(self):
        text = "Call me at (555) 123-4567"
        results = scan_text_for_pii(text)
        assert len(results) == 1
        assert results[0].pattern_type == 'phone_us'

    def test_scan_text_no_pii(self):
        text = "This is a normal sentence with no PII."
        results = scan_text_for_pii(text)
        assert len(results) == 0

    def test_scan_csv_file(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("id,name,email\n1,John,test@example.com")
        results = scan_csv_file(csv_file)
        assert len(results) >= 1
        assert any(r.pattern_type == 'email' for r in results)

    def test_scan_json_file(self, tmp_path):
        json_file = tmp_path / "test.json"
        json_file.write_text('{"email": "user@test.com", "name": "Test"}')
        results = scan_json_file(json_file)
        assert len(results) >= 1
        assert any(r.pattern_type == 'email' for r in results)

    def test_scan_directory(self, tmp_path):
        # Create test files
        (tmp_path / "subdir").mkdir()
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("id,email\n1,test@example.com")
        json_file = tmp_path / "subdir/data.json"
        json_file.write_text('{"ssn": "123-45-6789"}')
        
        results = scan_directory_for_pii(tmp_path)
        assert len(results) >= 2

    def test_generate_security_report(self, tmp_path):
        from code.security.pii_scanner import PIIResult
        
        results = [
            PIIResult(
                file_path="test.csv",
                line_number=1,
                pattern_type="email",
                matched_text="test@example.com",
                context="email: test@example.com"
            )
        ]
        
        output_file = tmp_path / "report.json"
        report = generate_security_report(results, output_file)
        
        assert output_file.exists()
        assert report["total_pii_found"] == 1
        assert len(report["leaks"]) == 1

    def test_run_pii_security_check_clean(self, tmp_path):
        # Create a clean directory
        clean_file = tmp_path / "clean.csv"
        clean_file.write_text("id,value\n1,100\n2,200")
        
        output_file = tmp_path / "report.json"
        report = run_pii_security_check(tmp_path, output_file)
        
        assert report["total_pii_found"] == 0
        assert report["leaks"] == []
        assert output_file.exists()
        
        # Verify JSON content
        with open(output_file) as f:
            data = json.load(f)
            assert data["leaks"] == []

    def test_pii_scan_output_format(self, tmp_path):
        """Test that the output matches the expected format for T042."""
        clean_file = tmp_path / "data.csv"
        clean_file.write_text("trial_id,response_time,stimulus_id\n1,250,prime_1\n2,300,prime_2")
        
        output_file = tmp_path / "pii_scan.json"
        run_pii_security_check(tmp_path, output_file)
        
        with open(output_file) as f:
            report = json.load(f)
        
        # Verify the exact format required by T042
        assert "leaks" in report
        assert report["leaks"] == []
        assert report["total_pii_found"] == 0

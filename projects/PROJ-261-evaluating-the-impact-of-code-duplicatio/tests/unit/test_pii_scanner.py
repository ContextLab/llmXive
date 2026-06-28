"""
Unit tests for PII scanner functionality.

Tests verify that the PII scanner correctly detects various PII patterns
in code files and data files. These tests must pass before the PII scanner
can be used in production.

Per Constitution Principle III (Data Hygiene), PII must be detected and
logged before any downstream processing occurs.

Related tasks: T017 (implementation), T052 (integration validation)
"""
import csv
import logging
import os
import re
import tempfile
from pathlib import Path
from typing import List, Dict, Any
import pytest

# Import the PII scanner module
from pii_scanner import (
    setup_logging,
    should_scan_file,
    scan_file_for_pii,
    scan_directory,
    write_findings_to_csv,
    run_pii_scan,
    main
)

# PII patterns that the scanner should detect
PII_PATTERNS = {
    'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    'phone': r'\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b',
    'ssn': r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b',
    'credit_card': r'\b(?:\d{4}[-.\s]?){3}\d{4}\b',
    'api_key': r'(?:api[_-]?key|apikey|api_secret|secret[_-]?key|access[_-]?token)[\s]*[:=][\s]*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
    'aws_key': r'\bAKIA[0-9A-Z]{16}\b',
    'password': r'(?:password|passwd|pwd)[\s]*[:=][\s]*["\']?([^\s"\']{4,})["\']?',
}

class TestPIIScannerShouldScanFile:
    """Test should_scan_file function for file type filtering."""
    
    def test_should_scan_python_file(self):
        """Python files should be scanned for PII."""
        assert should_scan_file(Path("test.py")) is True
        assert should_scan_file(Path("src/main.py")) is True
        assert should_scan_file(Path("data/file.py")) is True
    
    def test_should_scan_csv_file(self):
        """CSV files should be scanned for PII."""
        assert should_scan_file(Path("data.csv")) is True
        assert should_scan_file(Path("data/file.csv")) is True
    
    def test_should_scan_json_file(self):
        """JSON files should be scanned for PII."""
        assert should_scan_file(Path("config.json")) is True
        assert should_scan_file(Path("data/file.json")) is True
    
    def test_should_scan_txt_file(self):
        """Text files should be scanned for PII."""
        assert should_scan_file(Path("readme.txt")) is True
        assert should_scan_file(Path("data/notes.txt")) is True
    
    def test_should_not_scan_binary_file(self):
        """Binary files should not be scanned."""
        assert should_scan_file(Path("data.bin")) is False
        assert should_scan_file(Path("image.png")) is False
        assert should_scan_file(Path("model.pt")) is False
    
    def test_should_not_scan_pyc_file(self):
        """Compiled Python files should not be scanned."""
        assert should_scan_file(Path("test.pyc")) is False
    
    def test_should_not_scan_log_file(self):
        """Log files should not be scanned (they are outputs)."""
        assert should_scan_file(Path("app.log")) is False
    
    def test_should_not_scan_empty_extension(self):
        """Files without extension should be scanned."""
        assert should_scan_file(Path("Makefile")) is True
        assert should_scan_file(Path("requirements")) is True
    
    def test_should_scan_nested_directory_python(self):
        """Python files in nested directories should be scanned."""
        assert should_scan_file(Path("projects/PROJ-261/code/main.py")) is True
        assert should_scan_file(Path("data/processed/clone_metrics.csv")) is True

class TestPIIScannerScanFileForPII:
    """Test scan_file_for_pii function for PII detection."""
    
    def test_detect_email_address(self):
        """Email addresses should be detected."""
        content = "Contact: john.doe@example.com for support"
        findings = scan_file_for_pii("test.py", content)
        assert len(findings) > 0
        email_findings = [f for f in findings if f['pattern_type'] == 'email']
        assert len(email_findings) == 1
        assert 'john.doe@example.com' in email_findings[0]['match']
    
    def test_detect_multiple_emails(self):
        """Multiple email addresses should all be detected."""
        content = """
        Email: alice@example.com
        CC: bob@test.org
        BCC: charlie@company.net
        """
        findings = scan_file_for_pii("test.py", content)
        email_findings = [f for f in findings if f['pattern_type'] == 'email']
        assert len(email_findings) == 3
    
    def test_detect_ssn(self):
        """Social Security Numbers should be detected."""
        content = "SSN: 123-45-6789"
        findings = scan_file_for_pii("test.py", content)
        ssn_findings = [f for f in findings if f['pattern_type'] == 'ssn']
        assert len(ssn_findings) == 1
        assert '123-45-6789' in ssn_findings[0]['match']
    
    def test_detect_ssn_without_dashes(self):
        """SSN without dashes should be detected."""
        content = "SSN: 123456789"
        findings = scan_file_for_pii("test.py", content)
        ssn_findings = [f for f in findings if f['pattern_type'] == 'ssn']
        assert len(ssn_findings) == 1
    
    def test_detect_phone_number(self):
        """Phone numbers should be detected."""
        content = "Call us at 555-123-4567"
        findings = scan_file_for_pii("test.py", content)
        phone_findings = [f for f in findings if f['pattern_type'] == 'phone']
        assert len(phone_findings) >= 1
        assert '555-123-4567' in phone_findings[0]['match']
    
    def test_detect_phone_with_country_code(self):
        """Phone numbers with country code should be detected."""
        content = "International: +1-555-123-4567"
        findings = scan_file_for_pii("test.py", content)
        phone_findings = [f for f in findings if f['pattern_type'] == 'phone']
        assert len(phone_findings) >= 1
    
    def test_detect_api_key_pattern(self):
        """API key patterns should be detected."""
        content = "api_key = 'sk-1234567890abcdef1234567890abcdef'"
        findings = scan_file_for_pii("test.py", content)
        api_findings = [f for f in findings if f['pattern_type'] == 'api_key']
        assert len(api_findings) >= 1
    
    def test_detect_aws_access_key(self):
        """AWS access keys should be detected."""
        content = "AWS_KEY = 'AKIAIOSFODNN7EXAMPLE'"
        findings = scan_file_for_pii("test.py", content)
        aws_findings = [f for f in findings if f['pattern_type'] == 'aws_key']
        assert len(aws_findings) >= 1
    
    def test_detect_password_in_config(self):
        """Password patterns should be detected."""
        content = "password = 'secretpassword123'"
        findings = scan_file_for_pii("test.py", content)
        password_findings = [f for f in findings if f['pattern_type'] == 'password']
        assert len(password_findings) >= 1
    
    def test_no_pii_in_clean_file(self):
        """Files without PII should return empty findings."""
        content = """
        def hello_world():
            print("Hello, World!")
            return 42
        """
        findings = scan_file_for_pii("test.py", content)
        assert len(findings) == 0
    
    def test_empty_file_no_pii(self):
        """Empty files should return empty findings."""
        findings = scan_file_for_pii("empty.py", "")
        assert len(findings) == 0
    
    def test_whitespace_only_file(self):
        """Files with only whitespace should return empty findings."""
        content = "\n\n\n   \t\t  \n"
        findings = scan_file_for_pii("whitespace.py", content)
        assert len(findings) == 0
    
    def test_findings_include_file_path(self):
        """Findings should include the file path where PII was found."""
        content = "email: test@example.com"
        findings = scan_file_for_pii("data/user.py", content)
        assert len(findings) > 0
        assert findings[0]['file_path'] == 'data/user.py'
    
    def test_findings_include_line_number(self):
        """Findings should include line number where PII was found."""
        content = """line1
        line2 with email: test@example.com
        line3"""
        findings = scan_file_for_pii("test.py", content)
        assert len(findings) > 0
        assert 'line_number' in findings[0]
    
    def test_findings_include_pattern_type(self):
        """Findings should include the type of PII pattern detected."""
        content = "email: test@example.com"
        findings = scan_file_for_pii("test.py", content)
        assert len(findings) > 0
        assert 'pattern_type' in findings[0]
        assert findings[0]['pattern_type'] == 'email'
    
    def test_findings_include_match_text(self):
        """Findings should include the matched PII text (redacted)."""
        content = "email: test@example.com"
        findings = scan_file_for_pii("test.py", content)
        assert len(findings) > 0
        assert 'match' in findings[0]
        assert findings[0]['match'] is not None
    
    def test_findings_include_timestamp(self):
        """Findings should include timestamp of detection."""
        content = "email: test@example.com"
        findings = scan_file_for_pii("test.py", content)
        assert len(findings) > 0
        assert 'timestamp' in findings[0]
    
    def test_findings_include_severity(self):
        """Findings should include severity level."""
        content = "SSN: 123-45-6789"
        findings = scan_file_for_pii("test.py", content)
        assert len(findings) > 0
        assert 'severity' in findings[0]
    
    def test_high_severity_for_ssn(self):
        """SSN should be marked as high severity."""
        content = "SSN: 123-45-6789"
        findings = scan_file_for_pii("test.py", content)
        ssn_findings = [f for f in findings if f['pattern_type'] == 'ssn']
        assert len(ssn_findings) == 1
        assert ssn_findings[0]['severity'] in ['high', 'critical']
    
    def test_high_severity_for_api_keys(self):
        """API keys should be marked as high severity."""
        content = "api_key = 'sk-1234567890abcdef1234567890abcdef'"
        findings = scan_file_for_pii("test.py", content)
        api_findings = [f for f in findings if f['pattern_type'] == 'api_key']
        assert len(api_findings) >= 1
        assert api_findings[0]['severity'] in ['high', 'critical']

class TestPIIScannerScanDirectory:
    """Test scan_directory function for directory scanning."""
    
    def test_scan_single_directory(self):
        """Should scan files in a single directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("email: test@example.com")
            
            findings = scan_directory(Path(tmpdir))
            assert len(findings) > 0
    
    def test_scan_nested_directories(self):
        """Should recursively scan nested directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = Path(tmpdir) / "nested" / "deep"
            nested_dir.mkdir(parents=True)
            test_file = nested_dir / "test.py"
            test_file.write_text("email: nested@example.com")
            
            findings = scan_directory(Path(tmpdir))
            assert len(findings) > 0
    
    def test_scan_multiple_files(self):
        """Should scan multiple files in a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "file1.py"
            file2 = Path(tmpdir) / "file2.py"
            file1.write_text("email: file1@example.com")
            file2.write_text("email: file2@example.com")
            
            findings = scan_directory(Path(tmpdir))
            assert len(findings) >= 2
    
    def test_skip_binary_files(self):
        """Should skip binary files in directory scan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "test.py"
            bin_file = Path(tmpdir) / "data.bin"
            py_file.write_text("email: test@example.com")
            bin_file.write_bytes(b'\x00\x01\x02\x03')
            
            findings = scan_directory(Path(tmpdir))
            # Should only find PII in the Python file, not binary
            assert len(findings) >= 1
    
    def test_skip_pyc_files(self):
        """Should skip .pyc files in directory scan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "test.py"
            pyc_file = Path(tmpdir) / "test.pyc"
            py_file.write_text("email: test@example.com")
            pyc_file.write_bytes(b'\x00\x01\x02\x03')
            
            findings = scan_directory(Path(tmpdir))
            # Should only find PII in the .py file
            assert len(findings) >= 1
    
    def test_empty_directory(self):
        """Should handle empty directories gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            findings = scan_directory(Path(tmpdir))
            assert len(findings) == 0
    
    def test_nonexistent_directory(self):
        """Should handle nonexistent directories gracefully."""
        findings = scan_directory(Path("/nonexistent/path/that/does/not/exist"))
        assert len(findings) == 0
    
    def test_findings_include_source_directory(self):
        """Findings should include the source directory path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("email: test@example.com")
            
            findings = scan_directory(Path(tmpdir))
            assert len(findings) > 0
            # Verify file path is included
            assert any(f['file_path'] == str(test_file) for f in findings)

class TestPIIScannerWriteFindingsToCsv:
    """Test write_findings_to_csv function."""
    
    def test_write_findings_creates_file(self):
        """Should create CSV file with findings."""
        with tempfile.TemporaryDirectory() as tmpdir:
          csv_path = Path(tmpdir) / "findings.csv"
          findings = [
              {
                  'file_path': 'test.py',
                  'pattern_type': 'email',
                  'match': 'test@example.com',
                  'severity': 'medium'
              }
          ]
          write_findings_to_csv(findings, csv_path)
          assert csv_path.exists()
    
    def test_write_findings_has_correct_headers(self):
        """CSV should have correct column headers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "findings.csv"
            findings = [{'file_path': 'test.py', 'pattern_type': 'email'}]
            write_findings_to_csv(findings, csv_path)
            
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                assert 'file_path' in headers
                assert 'pattern_type' in headers
    
    def test_write_empty_findings(self):
        """Should handle empty findings list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "findings.csv"
            write_findings_to_csv([], csv_path)
            assert csv_path.exists()
    
    def test_write_multiple_findings(self):
        """Should write all findings to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "findings.csv"
            findings = [
                {'file_path': 'file1.py', 'pattern_type': 'email', 'match': 'a@b.com'},
                {'file_path': 'file2.py', 'pattern_type': 'phone', 'match': '555-1234'},
                {'file_path': 'file3.py', 'pattern_type': 'ssn', 'match': '123-45-6789'}
            ]
            write_findings_to_csv(findings, csv_path)
            
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 3

class TestPIIScannerRunPIIScan:
    """Test run_pii_scan function."""
    
    def test_run_scan_on_directory(self):
        """Should run PII scan on specified directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("email: test@example.com")
            
            findings = run_pii_scan(Path(tmpdir))
            assert len(findings) > 0
    
    def test_run_scan_returns_findings(self):
        """Should return list of findings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("email: test@example.com")
            
            findings = run_pii_scan(Path(tmpdir))
            assert isinstance(findings, list)
            assert all(isinstance(f, dict) for f in findings)
    
    def test_run_scan_no_pii(self):
        """Should return empty list when no PII found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("print('Hello, World!')")
            
            findings = run_pii_scan(Path(tmpdir))
            assert len(findings) == 0

class TestPIIScannerEdgeCases:
    """Test edge cases and error handling."""
    
    def test_unicode_content(self):
        """Should handle unicode content correctly."""
        content = "email: 测试@example.com"
        findings = scan_file_for_pii("test.py", content)
        assert len(findings) >= 1
    
    def test_multiline_content(self):
        """Should handle multiline content correctly."""
        content = """
        Line 1: No PII here
        Line 2: email@test.com
        Line 3: More code
        """
        findings = scan_file_for_pii("test.py", content)
        assert len(findings) >= 1
    
    def test_large_file_simulation(self):
        """Should handle large content without memory issues."""
        content = "email: test@example.com\n" * 1000
        findings = scan_file_for_pii("large.py", content)
        assert len(findings) >= 1
    
    def test_special_characters_in_pii(self):
        """Should handle special characters in PII patterns."""
        content = "email: user+tag@sub.domain.co.uk"
        findings = scan_file_for_pii("test.py", content)
        assert len(findings) >= 1
    
    def test_false_positive_prevention(self):
        """Should not flag non-PII patterns as PII."""
        content = """
        def calculate_ssn_factor(x):
            return x * 123456789
        
        def get_phone_number():
            return "555"
        """
        findings = scan_file_for_pii("test.py", content)
        # Should not detect SSN or phone in these function names
        ssn_findings = [f for f in findings if f['pattern_type'] == 'ssn']
        phone_findings = [f for f in findings if f['pattern_type'] == 'phone']
        # These should be empty or minimal (function names shouldn't match)
        assert len(ssn_findings) == 0
        assert len(phone_findings) == 0
    
    def test_partial_matches(self):
        """Should not match partial patterns."""
        content = "This is not an email: test@"
        findings = scan_file_for_pii("test.py", content)
        email_findings = [f for f in findings if f['pattern_type'] == 'email']
        assert len(email_findings) == 0

class TestPIIScannerLogging:
    """Test logging behavior."""
    
    def test_logging_setup(self):
        """Should setup logging correctly."""
        logger = setup_logging("test_pii_scanner.log")
        assert logger is not None
        assert logger.name == "pii_scanner"
    
    def test_logging_levels(self):
        """Should log at appropriate levels."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = setup_logging(str(log_path))
            
            logger.info("Test info message")
            logger.warning("Test warning message")
            logger.error("Test error message")
            
            assert log_path.exists()
            with open(log_path, 'r') as f:
                content = f.read()
                assert "INFO" in content
                assert "WARNING" in content
                assert "ERROR" in content

class TestPIIScannerConstitutionCompliance:
    """Test Constitution Principle III (Data Hygiene) compliance."""
    
    def test_all_pii_detected(self):
        """All PII types should be detectable."""
        test_cases = [
            ("email@example.com", "email"),
            ("123-45-6789", "ssn"),
            ("555-123-4567", "phone"),
            ("AKIAIOSFODNN7EXAMPLE", "aws_key"),
        ]
        for content, pattern_type in test_cases:
            findings = scan_file_for_pii("test.py", content)
            matching_findings = [f for f in findings if f['pattern_type'] == pattern_type]
            assert len(matching_findings) >= 1, f"Failed to detect {pattern_type}: {content}"
    
    def test_pii_logged_for_audit(self):
        """All PII findings should be loggable for audit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "audit_findings.csv"
            findings = [
                {
                    'file_path': 'data.py',
                    'pattern_type': 'email',
                    'match': 'audit@example.com',
                    'severity': 'medium',
                    'timestamp': '2024-01-01T00:00:00'
                }
            ]
            write_findings_to_csv(findings, csv_path)
            assert csv_path.exists()
            assert csv_path.stat().st_size > 0
    
    def test_pii_severity_classification(self):
        """PII should be classified by severity."""
        content = "SSN: 123-45-6789"
        findings = scan_file_for_pii("test.py", content)
        assert len(findings) > 0
        assert all('severity' in f for f in findings)
        assert any(f['severity'] in ['high', 'critical'] for f in findings)

class TestPIIScannerIntegration:
    """Integration tests for PII scanner workflow."""
    
    def test_full_scan_workflow(self):
        """Test complete scan workflow from directory to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            file1 = Path(tmpdir) / "file1.py"
            file2 = Path(tmpdir) / "file2.py"
            file1.write_text("email: file1@example.com")
            file2.write_text("email: file2@example.com\nSSN: 123-45-6789")
            
            # Run scan
            findings = run_pii_scan(Path(tmpdir))
            assert len(findings) >= 2
            
            # Write to CSV
            csv_path = Path(tmpdir) / "findings.csv"
            write_findings_to_csv(findings, csv_path)
            assert csv_path.exists()
            
            # Verify CSV content
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) >= 2
    
    def test_scan_data_directories(self):
        """Should scan data directories as per Constitution Principle III."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Simulate data directory structure
            raw_dir = Path(tmpdir) / "raw"
            processed_dir = Path(tmpdir) / "processed"
            analysis_dir = Path(tmpdir) / "analysis"
            raw_dir.mkdir()
            processed_dir.mkdir()
            analysis_dir.mkdir()
            
            # Add files with PII
            (raw_dir / "raw_data.py").write_text("email: raw@example.com")
            (processed_dir / "processed.py").write_text("email: processed@example.com")
            (analysis_dir / "analysis.py").write_text("email: analysis@example.com")
            
            # Scan all data directories
            for data_dir in [raw_dir, processed_dir, analysis_dir]:
                findings = run_pii_scan(data_dir)
                assert len(findings) >= 1, f"No PII found in {data_dir}"

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
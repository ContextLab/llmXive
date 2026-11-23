import os
import sys
import json
import tempfile
from pathlib import Path
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from security.pii_scanner import (
    scan_file_for_pii,
    scan_directory_for_pii,
    generate_pii_report,
    enforce_pii_policy,
    run_pii_scan_pipeline,
    PII_PATTERNS
)

@pytest.fixture
def temp_test_files():
    """Create temporary test files with various PII patterns."""
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    
    # File with email
    email_file = temp_path / "email_test.txt"
    email_file.write_text("Contact: user@example.com for support.\nAnother: admin@test.org")
    
    # File with API key
    api_file = temp_path / "config.json"
    api_file.write_text('{"api_key": "sk-1234567890abcdef1234567890abcdef", "debug": true}')
    
    # File with GitHub token
    token_file = temp_path / "tokens.txt"
    token_file.write_text("GH_TOKEN=ghp_1234567890abcdefghijklmnopqrstuvwxyz123456")
    
    # File with SSN
    ssn_file = temp_path / "records.csv"
    ssn_file.write_text("name,ssn\nJohn Doe,123-45-6789\nJane Smith,987-65-4321")
    
    # Clean file
    clean_file = temp_path / "clean.py"
    clean_file.write_text("def hello():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    hello()")
    
    return temp_path

def test_scan_file_for_pii_email(temp_test_files):
    """Test email detection in a file."""
    file_path = temp_test_files / "email_test.txt"
    findings = scan_file_for_pii(file_path)
    
    assert len(findings) >= 2, "Should detect at least 2 email addresses"
    assert any(f['pattern_type'] == 'email' for f in findings)
    
    for finding in findings:
        assert '@' in finding['match_text']
        assert finding['file'] == str(file_path)

def test_scan_file_for_pii_api_key(temp_test_files):
    """Test API key detection."""
    file_path = temp_test_files / "config.json"
    findings = scan_file_for_pii(file_path)
    
    assert len(findings) >= 1, "Should detect at least 1 API key pattern"
    assert any(f['pattern_type'] == 'api_key' for f in findings)

def test_scan_file_for_pii_github_token(temp_test_files):
    """Test GitHub token detection."""
    file_path = temp_test_files / "tokens.txt"
    findings = scan_file_for_pii(file_path)
    
    assert len(findings) >= 1, "Should detect GitHub token"
    assert any(f['pattern_type'] == 'github_token' for f in findings)
    assert 'ghp_' in findings[0]['match_text']

def test_scan_file_for_pii_ssn(temp_test_files):
    """Test SSN detection."""
    file_path = temp_test_files / "records.csv"
    findings = scan_file_for_pii(file_path)
    
    assert len(findings) >= 2, "Should detect at least 2 SSNs"
    assert all(f['pattern_type'] == 'ssn' for f in findings)

def test_scan_file_for_pii_clean_file(temp_test_files):
    """Test that clean files return no findings."""
    file_path = temp_test_files / "clean.py"
    findings = scan_file_for_pii(file_path)
    
    # Should have no PII findings
    assert len(findings) == 0, "Clean file should have no PII findings"

def test_scan_directory_for_pii(temp_test_files):
    """Test directory scanning."""
    findings = scan_directory_for_pii(temp_test_files)
    
    assert len(findings) >= 5, "Should find multiple PII instances across files"
    
    # Check that multiple file types were scanned
    files_scanned = set(f['file'] for f in findings)
    assert len(files_scanned) >= 4, "Should scan multiple files"

def test_generate_pii_report(temp_test_files):
    """Test report generation."""
    findings = scan_directory_for_pii(temp_test_files)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_report.json"
        report = generate_pii_report(findings, output_path)
        
        assert 'summary' in report
        assert 'findings' in report
        assert report['summary']['total_findings'] > 0
        assert report['summary']['files_affected_count'] > 0
        
        # Verify file was written
        assert output_path.exists()
        
        # Verify JSON is valid
        with open(output_path) as f:
            loaded = json.load(f)
            assert loaded == report

def test_enforce_pii_policy_critical():
    """Test policy enforcement with critical findings."""
    findings = [
        {'pattern_type': 'github_token', 'severity': 'critical'},
        {'pattern_type': 'ssn', 'severity': 'critical'}
    ]
    
    is_compliant, message = enforce_pii_policy(findings, block_on_critical=True)
    
    assert not is_compliant
    assert 'critical' in message.lower()

def test_enforce_pii_policy_no_critical():
    """Test policy enforcement with no critical findings."""
    findings = [
        {'pattern_type': 'email', 'severity': 'medium'},
        {'pattern_type': 'ip_address', 'severity': 'low'}
    ]
    
    is_compliant, message = enforce_pii_policy(findings, block_on_critical=True)
    
    assert is_compliant
    assert 'passed' in message.lower()

def test_run_pii_scan_pipeline(temp_test_files):
    """Test full pipeline execution."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        result = run_pii_scan_pipeline(
            scan_paths=[temp_test_files],
            output_dir=output_dir,
            block_on_critical=False
        )
        
        assert 'status' in result
        assert 'message' in result
        assert 'report_path' in result
        assert 'summary' in result
        assert result['status'] in ['passed', 'failed']
        
        # Verify report was created
        assert Path(result['report_path']).exists()

def test_run_pii_scan_pipeline_fails_on_critical(temp_test_files):
    """Test pipeline fails when critical findings exist and blocking is enabled."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        result = run_pii_scan_pipeline(
            scan_paths=[temp_test_files],
            output_dir=output_dir,
            block_on_critical=True
        )
        
        assert result['status'] == 'failed'
        assert 'critical' in result['message'].lower()

def test_exclude_directories(temp_test_files):
    """Test that specified directories are excluded."""
    # Create a subdirectory with PII
    sub_dir = temp_test_files / "subdir"
    sub_dir.mkdir()
    (sub_dir / "secret.txt").write_text("token=ghp_secret123")
    
    # Scan excluding the subdirectory
    findings = scan_directory_for_pii(temp_test_files, exclude_dirs=['subdir'])
    
    # Should not find PII in the excluded directory
    for finding in findings:
        assert 'subdir' not in finding['file']

def test_extension_filtering(temp_test_files):
    """Test that only specified extensions are scanned."""
    # Create a .py file with PII
    py_file = temp_test_files / "secret.py"
    py_file.write_text("api_key = 'secret123'")
    
    # Scan only .txt files
    findings = scan_directory_for_pii(temp_test_files, extensions=['.txt'])
    
    # Should not find the .py file
    for finding in findings:
        assert not finding['file'].endswith('.py')

if __name__ == '__main__':
    pytest.main([__file__, '-v'])

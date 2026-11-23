"""
Tests for security scanner module.
"""
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the scanner functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))
from security_scanner import scan_file, scan_directory, generate_report, KEY_PATTERNS, SAFE_PATTERNS

class TestSecurityScanner:
    """Test cases for security scanning functionality."""

    def test_scan_file_no_secrets(self, tmp_path):
        """Test scanning a file with no hardcoded secrets."""
        safe_file = tmp_path / "safe.py"
        safe_content = """
import os
API_KEY = os.environ.get('API_KEY')
password = os.getenv('PASSWORD')
# This is a comment about API keys
config = {'key': 'value'}
"""
        safe_file.write_text(safe_content)
        
        findings = scan_file(safe_file)
        assert len(findings) == 0

    def test_scan_file_hardcoded_key(self, tmp_path):
        """Test scanning a file with hardcoded API key."""
        bad_file = tmp_path / "bad.py"
        bad_content = """
import os
API_KEY = "sk_live_1234567890abcdef"
password = "supersecret123"
"""
        bad_file.write_text(bad_content)
        
        findings = scan_file(bad_file)
        assert len(findings) > 0
        assert any('sk_live' in f['content'] for f in findings)

    def test_scan_file_hardcoded_password(self, tmp_path):
        """Test scanning a file with hardcoded password."""
        bad_file = tmp_path / "bad_pass.py"
        bad_content = """
PASSWORD = "my_secret_password_123"
secret_key = 'abc123def456'
"""
        bad_file.write_text(bad_content)
        
        findings = scan_file(bad_file)
        assert len(findings) > 0
        assert any('my_secret_password' in f['content'] for f in findings)

    def test_scan_file_env_var_safe(self, tmp_path):
        """Test that environment variable access is considered safe."""
        safe_file = tmp_path / "safe_env.py"
        safe_content = """
import os
API_KEY = os.environ.get('DRYAD_API_KEY')
token = os.environ['ANAGE_API_KEY']
"""
        safe_file.write_text(safe_content)
        
        findings = scan_file(safe_file)
        assert len(findings) == 0

    def test_scan_directory(self, tmp_path):
        """Test scanning a directory with multiple files."""
        # Create safe file
        safe_file = tmp_path / "safe.py"
        safe_file.write_text("API_KEY = os.environ.get('KEY')")
        
        # Create bad file
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("SECRET = 'hardcoded_secret'")
        
        findings = scan_directory(tmp_path)
        assert len(findings) == 1
        assert findings[0]['file'].endswith('bad.py')

    def test_generate_report_empty(self):
        """Test report generation with no findings."""
        report = generate_report([])
        assert "PASSED" in report
        assert "No hardcoded secrets" in report

    def test_generate_report_with_findings(self):
        """Test report generation with findings."""
        findings = [
            {
                'file': 'test.py',
                'line': 10,
                'content': 'API_KEY = "secret123"',
                'pattern': 'test',
                'severity': 'HIGH'
            }
        ]
        report = generate_report(findings)
        assert "FAILED" in report
        assert "HIGH SEVERITY" in report
        assert "test.py:10" in report

    def test_aws_key_pattern(self, tmp_path):
        """Test detection of AWS-style keys."""
        bad_file = tmp_path / "aws.py"
        bad_content = """
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
"""
        bad_file.write_text(bad_content)
        
        findings = scan_file(bad_file)
        assert len(findings) > 0
        assert any('AKIA' in f['content'] for f in findings)

    def test_dryad_key_pattern(self, tmp_path):
        """Test detection of Dryad API key patterns."""
        bad_file = tmp_path / "dryad.py"
        bad_content = """
DRYAD_API_KEY = "dryad_secret_key_12345"
"""
        bad_file.write_text(bad_content)
        
        findings = scan_file(bad_file)
        assert len(findings) > 0

    def test_anage_key_pattern(self, tmp_path):
        """Test detection of AnAge API key patterns."""
        bad_file = tmp_path / "anage.py"
        bad_content = """
anage_api_key = "anage_token_67890"
"""
        bad_file.write_text(bad_content)
        
        findings = scan_file(bad_file)
        assert len(findings) > 0
        assert any('anage_token' in f['content'].lower() for f in findings)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
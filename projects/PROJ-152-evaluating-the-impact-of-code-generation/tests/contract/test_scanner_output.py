import pytest
import csv
import os
from pathlib import Path
import sys

# Add code dir to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analyze import run_bandit, detect_language
import tempfile

class TestScannerOutputContract:
    """
    Contract tests to ensure scanner output format is consistent.
    These tests verify that the scanner runners return a list of dicts 
    with the expected keys.
    """

    def test_bandit_output_format(self):
        """Test that Bandit returns a list of dicts with required keys."""
        sample_code = """
        import hashlib
        password = "secret"
        h = hashlib.md5(password.encode())
        """
        snippet_id = "test_snippet_1"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            findings = run_bandit(sample_code, snippet_id, Path(tmpdir))
            
            assert isinstance(findings, list), "Bandit should return a list"
            
            for finding in findings:
                assert isinstance(finding, dict), "Each finding should be a dict"
                required_keys = ["cwe_id", "raw_severity", "finding_text"]
                for key in required_keys:
                    assert key in finding, f"Missing key {key} in finding: {finding}"

    def test_detect_language_python(self):
        """Test language detection for Python."""
        code = "def hello(): pass"
        assert detect_language(code, "test") == "python"

    def test_detect_language_javascript(self):
        """Test language detection for JavaScript."""
        code = "function hello() { return 1; }"
        assert detect_language(code, "test") == "javascript"

    def test_detect_language_java(self):
        """Test language detection for Java."""
        code = "public class Test { public static void main() {} }"
        assert detect_language(code, "test") == "java"

    def test_empty_code_handling(self):
        """Test that empty code returns empty findings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            findings = run_bandit("", "test", Path(tmpdir))
            assert len(findings) == 0

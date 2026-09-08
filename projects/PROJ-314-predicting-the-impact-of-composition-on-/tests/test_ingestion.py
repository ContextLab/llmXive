import os
import sys
import pytest
import logging
from pathlib import Path
import time

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ingestion import validate_source_citations, ensure_output_dirs, validate_data_gap
from logger import setup_citation_logger

class TestT010b:
    """Test suite for T010b: Verify logs/citation_validation.log creation."""

    def setup_method(self):
        """Ensure clean state before each test."""
        self.log_path = Path("logs/citation_validation.log")
        if self.log_path.exists():
            self.log_path.unlink()
        ensure_output_dirs()

    def test_citation_validation_log_creation(self):
        """
        Execute validation with dummy URLs and assert log creation.
        Asserts that logs/citation_validation.log exists and contains
        at least one entry with format INFO: Citation validation for {url}: {status}.
        """
        dummy_urls = ['https://example.com']
        
        # Run validation
        results = validate_source_citations(dummy_urls)
        
        # Assert log file exists
        assert self.log_path.exists(), "logs/citation_validation.log was not created"
        
        # Assert log content
        content = self.log_path.read_text()
        assert "Citation validation for" in content, "Log does not contain expected entry format"
        
        # Assert specific URL and status format
        assert "https://example.com" in content, "Log does not contain the dummy URL"
        assert "VALID" in content or "UNREACHABLE" in content or "ERROR" in content, "Log does not contain a status"

    def test_log_format(self):
        """Verify the exact log format required by T010b."""
        dummy_urls = ['https://httpbin.org/status/200']
        validate_source_citations(dummy_urls)
        
        content = self.log_path.read_text()
        lines = content.strip().split('\n')
        
        found_valid_line = False
        for line in lines:
            if "Citation validation for" in line:
                # Check format: INFO: Citation validation for {url}: {status}
                # The logger.info adds the level, so we look for the message part
                assert "Citation validation for https://httpbin.org/status/200:" in line, f"Line format incorrect: {line}"
                found_valid_line = True
                break
        
        assert found_valid_line, "No valid log entry found in logs/citation_validation.log"
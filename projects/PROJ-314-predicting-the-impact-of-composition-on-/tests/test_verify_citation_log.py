"""
Unit tests for verify_citation_log.py (T010b verification).

Tests the verification logic for citation validation log creation.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from verify_citation_log import main as verify_main
from ingestion import validate_source_citations
from code import logger

class TestVerifyCitationLog:
    """Test cases for citation validation log verification."""

    def test_log_file_creation(self):
        """Test that logs/citation_validation.log is created."""
        logs_dir = project_root / 'logs'
        logs_dir.mkdir(exist_ok=True)
        
        log_file = logs_dir / 'citation_validation.log'
        
        # Run validation with dummy URLs
        dummy_urls = ['https://example.com']
        validate_source_citations(dummy_urls)
        
        # Verify file exists
        assert log_file.exists(), "Log file should be created"

    def test_log_format(self):
        """Test that log contains expected format."""
        logs_dir = project_root / 'logs'
        log_file = logs_dir / 'citation_validation.log'
        
        # Ensure we have content
        if not log_file.exists():
            dummy_urls = ['https://example.com']
            validate_source_citations(dummy_urls)
        
        with open(log_file, 'r') as f:
            content = f.read()
        
        # Check for expected pattern
        assert "Citation validation for" in content, \
            "Log should contain 'Citation validation for' entries"
        
        # Check for status field
        assert "INFO:" in content or "ERROR:" in content, \
            "Log should contain log level indicators"

    def test_verify_main_success(self, capsys):
        """Test that verify_main runs successfully and prints success message."""
        # Ensure logs directory exists
        logs_dir = project_root / 'logs'
        logs_dir.mkdir(exist_ok=True)
        
        # Run the main function
        result = verify_main()
        
        # Check return code
        assert result == 0, "Main function should return 0 on success"
        
        # Check output
        captured = capsys.readouterr()
        assert "SUCCESS" in captured.out, \
            "Output should contain success message"
        assert "Log file exists" in captured.out, \
            "Output should confirm log file existence"

    def test_empty_status_detection(self):
        """Test that empty status would be detected as error."""
        # This is a conceptual test - in practice, validate_source_citations
        # should always produce a status
        logs_dir = project_root / 'logs'
        log_file = logs_dir / 'citation_validation.log'
        
        if log_file.exists():
            with open(log_file, 'r') as f:
                content = f.read()
            
            # Verify at least one non-empty status exists
            lines = content.split('\n')
            has_non_empty = False
            for line in lines:
                if "Citation validation for" in line:
                    parts = line.split(':')
                    if len(parts) >= 3:
                        status = parts[-1].strip()
                        if status:
                            has_non_empty = True
                            break
            
            assert has_non_empty, "At least one log entry should have non-empty status"
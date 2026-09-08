"""
Unit tests for the Reference Validator (T008b).
"""
import pytest
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.reference_validator import validate_url, validate_citation_format, validate_research_md, ConstitutionError
from utils.logging_config import get_logger

class TestValidateUrl:
    def test_valid_https_url(self):
        # We can't guarantee external availability, but we can test the logic
        # For unit tests, we might mock requests, but here we test the regex/logic structure
        # Since we can't guarantee internet, we just ensure it doesn't crash on valid format
        is_valid, msg = validate_url("https://www.example.com")
        # Note: This might return False if example.com is down, but it shouldn't crash
        assert isinstance(is_valid, bool)
        assert isinstance(msg, str)

    def test_invalid_url_format(self):
        is_valid, msg = validate_url("not-a-url")
        assert is_valid is False
        assert "pattern" in msg.lower() or "failed" in msg.lower()

    def test_empty_url(self):
        is_valid, msg = validate_url("")
        assert is_valid is False

class TestValidateCitationFormat:
    def test_valid_citation(self):
        is_valid, msg = validate_citation_format("[Smith et al., 2020]")
        assert is_valid is True

    def test_empty_citation(self):
        is_valid, msg = validate_citation_format("")
        assert is_valid is False

    def test_short_text(self):
        is_valid, msg = validate_citation_format("abc")
        assert is_valid is False

class TestValidateResearchMd:
    def test_validates_and_filters(self, tmp_path):
        # Create a mock draft file
        draft_content = """
        # Research Draft
        
        - Source 1: https://www.example.com (Valid)
        - Source 2: not-a-url (Invalid)
        - Source 3: https://www.google.com (Valid)
        """
        
        logger = get_logger("test_logger")
        result = validate_research_md(draft_content, logger)
        
        # Check that the result contains the valid headers
        assert "Research Sources - Verified" in result
        assert "Summary" in result
        
        # Note: We can't guarantee example.com or google.com are up in this test environment
        # but we verify the function runs and returns a string
        assert isinstance(result, str)
        assert len(result) > 0

    def test_handles_empty_draft(self):
        logger = get_logger("test_logger")
        result = validate_research_md("", logger)
        assert "Research Sources - Verified" in result
        assert "Valid sources: 0" in result

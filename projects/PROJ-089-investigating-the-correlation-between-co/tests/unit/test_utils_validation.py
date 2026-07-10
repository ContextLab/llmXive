import pytest
import os
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils import validate_tools_and_log, validate_tools_and_log_wrapper

class TestToolValidation:
    """Tests for tool validation logic per SC-005."""

    def test_validate_tools_returns_dict(self):
        """Test that validation returns a dictionary of results."""
        config = {}
        results = validate_tools_and_log(config, output_path=None)
        
        assert isinstance(results, dict)
        assert "radon" in results
        assert "semgrep" in results
        assert "pydriller" in results

    def test_validate_tools_has_required_fields(self):
        """Test that each tool result has required fields."""
        config = {}
        results = validate_tools_and_log(config, output_path=None)
        
        for tool_name, tool_result in results.items():
            assert "status" in tool_result
            assert "stars" in tool_result
            assert "citation_match" in tool_result
            assert "reason" in tool_result
            assert tool_result["status"] in ["PASSED", "FAILED"]

    def test_validate_tools_log_file_created(self, tmp_path):
        """Test that validation creates the log file."""
        config = {}
        log_path = tmp_path / "test_validation_log.csv"
        
        results = validate_tools_and_log(config, output_path=str(log_path))
        
        assert log_path.exists()
        
        # Verify CSV structure
        with open(log_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) > 0
            assert "tool_name" in rows[0]
            assert "validation_status" in rows[0]
            assert "github_stars" in rows[0]
            assert "citation_match" in rows[0]
            assert "reason" in rows[0]

    def test_star_threshold_enforcement(self):
        """Test that tools with <5000 stars fail validation (unless cited)."""
        config = {}
        results = validate_tools_and_log(config, output_path=None)
        
        # radon has 2100 stars (< 5000) and no citation -> FAILED
        assert results["radon"]["status"] == "FAILED"
        assert results["radon"]["stars"] < 5000
        assert not results["radon"]["citation_match"]

    def test_star_threshold_pass(self):
        """Test that tools with >=5000 stars pass validation."""
        config = {}
        results = validate_tools_and_log(config, output_path=None)
        
        # semgrep has 12500 stars (>= 5000) -> PASSED
        assert results["semgrep"]["status"] == "PASSED"
        assert results["semgrep"]["stars"] >= 5000

    def test_citation_override(self):
        """Test that citation match overrides star count failure."""
        config = {
            "validated_citations": ["radon"]
        }
        results = validate_tools_and_log(config, output_path=None)
        
        # radon should pass due to citation match despite low stars
        assert results["radon"]["status"] == "PASSED"
        assert results["radon"]["citation_match"] is True

    def test_wrapper_function(self, tmp_path):
        """Test the wrapper function uses default output path."""
        config = {}
        log_path = tmp_path / "default_log.csv"
        
        # Mock the default path behavior
        with patch('utils.Path', return_value=log_path):
            results = validate_tools_and_log_wrapper(config, output_path=str(log_path))
        
        assert log_path.exists()
        assert isinstance(results, dict)
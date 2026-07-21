"""
Unit tests for quickstart validation functionality.
"""
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, mock_open
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from validate_quickstart import (
    load_quickstart_content,
    check_required_sections,
    extract_code_commands,
    validate_file_references,
    check_for_placeholders,
    verify_artifacts,
    run_validation
)

class TestQuickstartValidation:
    """Tests for quickstart validation functions."""

    def test_check_required_sections_all_present(self):
        """Test that all required sections are detected when present."""
        content = """
        # Quickstart Guide

        ## Prerequisites
        Some text

        ## Installation
        Some text

        ## Data Download
        Some text

        ## Ground Truth Derivation
        Some text

        ## Hard Instance Selection
        Some text

        ## Agent Execution
        Some text

        ## Metrics Calculation
        Some text

        ## Validation
        Some text
        """
        missing = check_required_sections(content)
        assert len(missing) == 0

    def test_check_required_sections_missing(self):
        """Test that missing sections are detected."""
        content = """
        # Quickstart Guide

        ## Prerequisites
        Some text

        ## Installation
        Some text
        """
        missing = check_required_sections(content)
        assert "Data Download" in missing
        assert "Ground Truth Derivation" in missing

    def test_extract_code_commands(self):
        """Test extraction of code commands from markdown."""
        content = """
        # Quickstart

        ```bash
        python code/data/download.py
        ```

        ```python
        from config import get_path
        print(get_path("data"))
        ```

        # Comment
        ```bash
        # This is a comment
        python code/main.py --help
        ```
        """
        commands = extract_code_commands(content)
        assert "python code/data/download.py" in commands
        assert "from config import get_path" in commands
        assert "print(get_path(\"data\"))" in commands
        assert "python code/main.py --help" in commands
        assert "# This is a comment" not in commands

    def test_check_for_placeholders(self):
        """Test detection of placeholders in content."""
        content = """
        # Quickstart

        TODO: Add more details
        FIXME: Fix this later
        """
        placeholders = check_for_placeholders(content)
        assert len(placeholders) > 0
        assert "TODO found in quickstart" in placeholders

    def test_check_for_placeholders_clean(self):
        """Test that clean content has no placeholders."""
        content = """
        # Quickstart

        This is a clean document with no placeholders.
        """
        placeholders = check_for_placeholders(content)
        assert len(placeholders) == 0

    def test_verify_artifacts(self):
        """Test artifact verification."""
        # Create temporary artifacts for testing
        test_artifacts = [
            "data/curated/hard_subset.jsonl",
            "data/curated/non_hard_subset.jsonl"
        ]
        
        # Mock file existence
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.side_effect = lambda x: str(x).endswith('hard_subset.jsonl')
            
            results = verify_artifacts(test_artifacts)
            assert results["data/curated/hard_subset.jsonl"] == True
            assert results["data/curated/non_hard_subset.jsonl"] == False

    def test_run_validation_structure(self):
        """Test that run_validation returns expected structure."""
        with patch('validate_quickstart.load_quickstart_content') as mock_load:
            mock_load.return_value = """
            # Quickstart

            ## Prerequisites
            ## Installation
            ## Data Download
            ## Ground Truth Derivation
            ## Hard Instance Selection
            ## Agent Execution
            ## Metrics Calculation
            ## Validation
            """
            
            with patch('validate_quickstart.verify_artifacts') as mock_verify:
                mock_verify.return_value = {
                    "data/curated/hard_subset.jsonl": True,
                    "data/curated/non_hard_subset.jsonl": True,
                    "data/curated/synthetic_issues.jsonl": True,
                    "data/curated/validation_report.md": True,
                    "data/results/final_metrics.json": True,
                    "paper/draft.md": True
                }
                
                with patch('pathlib.Path.mkdir'):
                    with patch('builtins.open', mock_open()) as mock_file:
                        results = run_validation()
                        
                        assert "status" in results
                        assert "start_time" in results
                        assert "end_time" in results
                        assert "duration_seconds" in results
                        assert "log_messages" in results
                        assert "sections_check" in results
                        assert "commands_check" in results
                        assert "artifact_verification" in results

                        # Should pass if all artifacts exist
                        assert results["status"] in ["PASSED", "FAILED", "ERROR"]
                        assert "Validation Successful" in results["log_messages"] or \
                               "Validation Failed" in results["log_messages"] or \
                               "ERROR" in results["log_messages"]

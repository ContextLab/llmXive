"""
Unit tests for the Quickstart Validation module (T040).
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# We need to add the code directory to the path to import validate_quickstart
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from validate_quickstart import (
    check_required_sections,
    extract_code_commands,
    validate_file_references,
    check_for_placeholders,
    run_validation
)


class TestCheckRequiredSections:
    def test_all_sections_present(self):
        content = """
        # Setup
        Some text.
        # Data Curation
        More text.
        # Agent Execution
        Even more text.
        # Analysis
        Final text.
        # Results
        End.
        """
        missing = check_required_sections(content)
        assert len(missing) == 0

    def test_missing_section(self):
        content = """
        # Setup
        Some text.
        # Data Curation
        More text.
        """
        missing = check_required_sections(content)
        assert "Agent Execution" in missing
        assert "Analysis" in missing

    def test_case_insensitive(self):
        content = """
        # SETUP
        # data curation
        # AGENT EXECUTION
        # analysis
        # RESULTS
        """
        missing = check_required_sections(content)
        assert len(missing) == 0


class TestExtractCodeCommands:
    def test_basic_extraction(self):
        content = """
        Here is a command:
        ```bash
        python code/download.py
        ```
        """
        commands = extract_code_commands(content)
        assert len(commands) == 1
        assert commands[0] == "python code/download.py"

    def test_multiple_commands(self):
        content = """
        ```bash
        python code/download.py
        python code/curate.py
        ```
        """
        commands = extract_code_commands(content)
        assert len(commands) == 2

    def test_ignores_comments(self):
        content = """
        ```bash
        # This is a comment
        python code/download.py
        ```
        """
        commands = extract_code_commands(content)
        assert len(commands) == 1


class TestCheckForPlaceholders:
    def test_no_placeholders(self):
        content = "This is a valid text."
        found = check_for_placeholders(content)
        assert len(found) == 0

    def test_todo_found(self):
        content = "Line 1\nLine 2 TODO: fix this\nLine 3"
        found = check_for_placeholders(content)
        assert len(found) == 1
        assert "TODO" in found[0]

    def test_placeholder_brackets(self):
        content = "Check [ ] this box"
        found = check_for_placeholders(content)
        assert len(found) == 1


class TestRunValidation:
    def test_run_validation_structure(self):
        # Run against the actual quickstart if it exists, or just check structure
        # This is an integration-style unit test
        report = run_validation()
        assert "status" in report
        assert "checks" in report
        assert "errors" in report
        assert isinstance(report["status"], str)
        assert report["status"] in ["passed", "failed"]
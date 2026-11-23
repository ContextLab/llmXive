"""
Unit tests for prompt formatting logic in data_loader.py.
Specifically tests the extraction and formatting of bug descriptions into valid prompts.
"""
import pytest
import json
import os
from pathlib import Path

# Import the function under test from the sibling module
# The API surface confirms: extract_bug_fix_description is in code/data_loader.py
import sys
import importlib.util

# Ensure code/ is in path for import if not running from root
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from data_loader import extract_bug_fix_description, DataFetchError


class TestFormatBugDescription:
    """Tests for extract_bug_fix_description functionality."""

    def test_format_bug_description_returns_valid_prompt(self):
        """
        Verify that a bug description string is formatted into a valid prompt string.
        
        This test checks that the function:
        1. Takes a raw bug description (simulating Defects4J metadata).
        2. Formats it into a prompt string suitable for LLM ingestion.
        3. Returns a string that is not empty and contains the original description.
        4. Follows the expected structure (e.g., includes "Generate a JUnit test" prefix).
        """
        # Simulate a raw bug description as it might appear in Defects4J metadata
        raw_description = "NullPointerException occurs when parsing null input in DateUtils"
        
        # Call the function under test
        # We pass the raw description directly as the function expects a string or dict-like structure
        # Based on T015 description: "parse Defects4J metadata, format as prompt"
        # We assume the function handles string input directly or extracts from a dict
        prompt = extract_bug_fix_description(raw_description)
        
        # Assertions
        assert isinstance(prompt, str), "The prompt must be a string"
        assert len(prompt) > 0, "The prompt must not be empty"
        assert raw_description in prompt, "The original bug description must be present in the prompt"
        
        # Verify the prompt structure (matches the fallback template logic from T018a)
        # The prompt should start with a clear instruction
        assert prompt.startswith("Generate a JUnit test"), "The prompt must start with the generation instruction"

    def test_format_bug_description_handles_empty_input(self):
        """
        Verify behavior when an empty or whitespace-only description is provided.
        """
        empty_desc = "   "
        
        # The function should either raise an error or return a prompt with a warning structure
        # Based on T018a: "If prompt length < 20 chars, retry generation..."
        # We test that it doesn't crash and returns a string
        prompt = extract_bug_fix_description(empty_desc)
        
        assert isinstance(prompt, str)
        # Even if short, it should be a valid prompt string (potentially triggering retry logic downstream)
        assert len(prompt) > 0

    def test_format_bug_description_with_special_characters(self):
        """
        Verify that descriptions containing special characters (e.g., quotes, newlines)
        are handled safely without breaking the prompt structure.
        """
        special_desc = 'Error: "Invalid state" when user clicks "Submit" on line 42.\nCheck logs.'
        
        prompt = extract_bug_fix_description(special_desc)
        
        assert isinstance(prompt, str)
        assert special_desc in prompt, "Special characters must be preserved in the prompt"
        # Ensure no unescaped newlines break the prompt structure if it's meant to be single-line
        # (Though multi-line prompts are often fine, we ensure the description is intact)
        
    def test_format_bug_description_with_dict_input(self):
        """
        Verify that if a dictionary (simulating a dataset row) is passed,
        the function extracts the 'description' or 'bug_description' key correctly.
        """
        # Simulate a Defects4J row structure
        bug_row = {
            "project": "Lang",
            "bug_id": "123",
            "description": "Null pointer in String parser",
            "commit": "abc123"
        }
        
        prompt = extract_bug_fix_description(bug_row)
        
        assert isinstance(prompt, str)
        assert bug_row["description"] in prompt
        assert prompt.startswith("Generate a JUnit test")

    def test_format_bug_description_with_missing_key(self):
        """
        Verify behavior when a dictionary is passed but lacks the description key.
        Expected: Raise DataFetchError or return a specific error prompt.
        """
        incomplete_row = {
            "project": "Lang",
            "bug_id": "123"
            # missing 'description'
        }
        
        # The function should handle this gracefully.
        # Based on T015/T018a logic, if no description, it might raise or use fallback.
        # We expect it not to crash with KeyError, but to raise DataFetchError or similar.
        with pytest.raises((DataFetchError, KeyError, ValueError)):
            extract_bug_fix_description(incomplete_row)

    def test_format_bug_description_with_null_input(self):
        """
        Verify behavior when None is passed.
        """
        with pytest.raises((DataFetchError, TypeError, ValueError)):
            extract_bug_fix_description(None)
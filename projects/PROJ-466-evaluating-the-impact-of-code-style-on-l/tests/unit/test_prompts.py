"""
Unit tests for prompt loading and validation.
"""
import pytest
from pathlib import Path

# Import the loader if it exists, or test file reading directly
# Since we are testing T010, we assume the prompts exist
PROMPTS_DIR = Path(__file__).parent.parent.parent / "code" / "prompts"

def test_prompt_files_exist():
    """Test that all required prompt files exist."""
    required_files = ["neutral.txt", "pep8.txt", "minified.txt"]
    for filename in required_files:
        filepath = PROMPTS_DIR / filename
        assert filepath.exists(), f"Prompt file {filename} does not exist"

def test_prompt_files_not_empty():
    """Test that all prompt files are not empty."""
    required_files = ["neutral.txt", "pep8.txt", "minified.txt"]
    for filename in required_files:
        filepath = PROMPTS_DIR / filename
        content = filepath.read_text()
        assert len(content.strip()) > 0, f"Prompt file {filename} is empty"

def test_neutral_prompt_no_pep8_enforcement():
    """Test that the neutral prompt does not enforce PEP 8."""
    filepath = PROMPTS_DIR / "neutral.txt"
    content = filepath.read_text().lower()
    # Check that it doesn't explicitly demand PEP 8 strictness
    assert "strict pep 8" not in content, "Neutral prompt should not enforce strict PEP 8"
    assert "4 spaces" not in content, "Neutral prompt should not mandate 4 spaces"

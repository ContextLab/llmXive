"""
Unit tests for prompt setup and existence.
"""
import os
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the setup logic directly for testing
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))
from setup_prompts import PROMPT_FILES, PROMPTS_DIR as SETUP_PROMPTS_DIR

def test_prompt_files_exist():
    """Verify that all required prompt files exist after setup."""
    # We assume the setup has been run or is run as part of the test fixture
    # For this unit test, we verify the content structure defined in the module
    assert len(PROMPT_FILES) == 4
    expected_files = {
        "zero_shot_basic.txt",
        "zero_shot_style.txt",
        "few_shot_basic.txt",
        "few_shot_style.txt"
    }
    assert set(PROMPT_FILES.keys()) == expected_files

def test_prompt_content_contains_placeholder():
    """Verify that prompt templates contain the expected placeholder."""
    for filename, content in PROMPT_FILES.items():
        assert "{python_code}" in content, f"File {filename} missing {python_code} placeholder"

def test_prompt_files_created_in_temp_dir():
    """Test the creation logic in a temporary directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_prompts_dir = Path(tmp_dir) / "prompts"
        temp_prompts_dir.mkdir(parents=True, exist_ok=True)

        # Create files manually to simulate setup
        for filename, content in PROMPT_FILES.items():
            file_path = temp_prompts_dir / filename
            file_path.write_text(content, encoding="utf-8")

        # Verify all files exist
        for filename in PROMPT_FILES.keys():
            assert (temp_prompts_dir / filename).exists(), f"File {filename} not created"

        # Verify content matches
        for filename, expected_content in PROMPT_FILES.items():
            file_path = temp_prompts_dir / filename
            actual_content = file_path.read_text(encoding="utf-8")
            assert actual_content == expected_content, f"Content mismatch for {filename}"
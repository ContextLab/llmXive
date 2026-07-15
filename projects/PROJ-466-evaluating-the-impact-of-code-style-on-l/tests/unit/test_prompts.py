import pytest
import os
from pathlib import Path
from config.loader import load_config

# Test fixtures
PROMPT_DIR = Path("code/prompts")
REQUIRED_STYLES = ["neutral", "pep8", "minified"]

def test_prompts_directory_exists():
    """Verify that the prompts directory exists."""
    assert PROMPT_DIR.exists(), f"Prompts directory not found at {PROMPT_DIR}"

def test_all_required_prompt_files_exist():
    """Verify that all required prompt files exist."""
    for style in REQUIRED_STYLES:
        prompt_file = PROMPT_DIR / f"{style}.txt"
        assert prompt_file.exists(), f"Missing required prompt file: {prompt_file}"

def test_prompt_files_are_non_empty():
    """Verify that all prompt files contain content."""
    for style in REQUIRED_STYLES:
        prompt_file = PROMPT_DIR / f"{style}.txt"
        content = prompt_file.read_text().strip()
        assert len(content) > 0, f"Prompt file {prompt_file} is empty"

def test_prompt_content_loads_correctly():
    """Verify that prompt content can be loaded and is valid text."""
    for style in REQUIRED_STYLES:
        prompt_file = PROMPT_DIR / f"{style}.txt"
        try:
            content = prompt_file.read_text(encoding='utf-8')
            assert isinstance(content, str), f"Prompt content for {style} is not a string"
        except Exception as e:
            pytest.fail(f"Failed to load prompt {prompt_file}: {e}")

def test_prompt_templates_match_spec_profile():
    """
    Verify that prompt files contain keywords matching their style profile.
    This is a basic validation that the content aligns with the expected style.
    """
    # Expected keywords based on style profiles
    style_keywords = {
        "neutral": ["def", "class", "return"],  # Neutral code structure
        "pep8": ["PEP 8", "style", "indentation", "spaces"],  # PEP8 specific
        "minified": ["minified", "compressed", "no spaces", "compact"]  # Minified specific
    }

    for style, keywords in style_keywords.items():
        prompt_file = PROMPT_DIR / f"{style}.txt"
        content = prompt_file.read_text().lower()
        
        # Check that at least one keyword from the expected set is present
        # This ensures the prompt is actually about the intended style
        found_keywords = [kw for kw in keywords if kw in content]
        assert len(found_keywords) > 0, (
            f"Prompt file {prompt_file} does not contain expected keywords for {style} style. "
            f"Expected one of: {keywords}"
        )

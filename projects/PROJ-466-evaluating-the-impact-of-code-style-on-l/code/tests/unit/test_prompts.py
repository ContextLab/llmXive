"""
Unit tests for prompt loading and validation (T010).
"""
import pytest
from pathlib import Path
import sys

# Ensure imports work
code_root = Path(__file__).parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

# Assuming prompts are stored as text files in code/prompts/
# We will simulate the loading logic here since the actual loader might be in a specific module
# or we just check file existence and content validity.

PROMPTS_DIR = code_root / "prompts"

def test_prompt_files_exist():
    """Verify that required prompt template files exist."""
    required_files = ["neutral.txt", "pep8.txt", "minified.txt"]
    for fname in required_files:
        fpath = PROMPTS_DIR / fname
        assert fpath.exists(), f"Prompt file {fname} not found at {fpath}"

def test_prompt_files_not_empty():
    """Verify that prompt template files are not empty."""
    required_files = ["neutral.txt", "pep8.txt", "minified.txt"]
    for fname in required_files:
        fpath = PROMPTS_DIR / fname
        content = fpath.read_text()
        assert len(content.strip()) > 0, f"Prompt file {fname} is empty"

def test_prompt_content_structure():
    """
    Verify that prompts contain expected placeholders or structure.
    This is a basic check; specific content requirements depend on spec.
    """
    pep8_path = PROMPTS_DIR / "pep8.txt"
    content = pep8_path.read_text()
    # Check that it mentions PEP8 or style constraints
    assert "PEP8" in content or "style" in content.lower() or "format" in content.lower(), \
        "PEP8 prompt does not seem to contain style instructions"
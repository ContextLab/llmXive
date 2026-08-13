"""
Contract test for T004: Verify README.md exists and contains required sections.
Ensures the top-level documentation is present and non-empty with key instructions.
"""
import os
import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
README_PATH = PROJECT_ROOT / "README.md"

REQUIRED_SECTIONS = [
  "Overview",
  "Quick Start",
  "Prerequisites",
  "Installation",
  "Running the Full Pipeline",
  "Project Structure",
]

REQUIRED_COMMANDS = [
  "poetry run python -m src.pipeline.run_all",
  "poetry run python -m src.pipeline.run_us1",
  "poetry run python -m src.pipeline.run_us2",
]

@pytest.fixture
def readme_content(self) -> str:
    if not README_PATH.exists():
        pytest.fail(f"README.md not found at {README_PATH}")
    return README_PATH.read_text(encoding="utf-8")

def test_readme_exists(self):
    assert README_PATH.exists(), "README.md must exist at project root"
    assert README_PATH.stat().st_size > 0, "README.md must not be empty"

def test_readme_contains_required_sections(self, readme_content: str):
    for section in REQUIRED_SECTIONS:
        # Case-insensitive search for section headers
        pattern = re.compile(rf"##\s+{re.escape(section)}", re.IGNORECASE)
        assert pattern.search(readme_content), f"README.md missing required section: '{section}'"

def test_readme_contains_pipeline_commands(self, readme_content: str):
    for cmd in REQUIRED_COMMANDS:
        assert cmd in readme_content, f"README.md missing required command: '{cmd}'"

def test_readme_contains_data_management_info(self, readme_content: str):
    assert "data/gsm8k" in readme_content, "README.md must reference data directory"
    assert "checksums" in readme_content.lower(), "README.md must mention checksum validation"

def test_readme_structure_valid(self, readme_content: str):
    # Basic check that the file looks like Markdown
    assert "# llmXive" in readme_content or "# llmXive" in readme_content, "README.md must have a top-level title"
    assert "```" in readme_content, "README.md should contain code blocks for commands"
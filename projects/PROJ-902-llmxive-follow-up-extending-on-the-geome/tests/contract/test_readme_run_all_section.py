"""Test that the project's README includes usage instructions for the run_all pipeline script.

The README is expected to contain a section that mentions how to invoke the
top‑level pipeline script `run_all.py`. This test checks for the presence of
the string ``run_all.py`` (case‑insensitive) and for a short description that
includes the word ``pipeline``. If the README does not contain these
elements, the contract test will fail, signalling that the documentation is
incomplete.
"""

import re
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def readme_path() -> Path:
    """Return the absolute path to the project's README.md."""
    # The test file resides in ``tests/contract``; the README is at the repository root.
    return Path(__file__).resolve().parents[2] / "README.md"


def test_readme_exists(readme_path: Path) -> None:
    """The README file must exist."""
    assert readme_path.is_file(), f"README.md not found at expected location: {readme_path}"


def test_readme_contains_run_all_section(readme_path: Path) -> None:
    """The README must contain usage instructions for ``run_all.py``."""
    content = readme_path.read_text(encoding="utf-8")

    # Look for a line mentioning the script name.
    script_mention = re.search(r"run_all\.py", content, re.IGNORECASE)
    assert script_mention is not None, (
        "README.md does not mention 'run_all.py'. "
        "Add a usage section that explains how to invoke the pipeline."
    )

    # Ensure the surrounding context includes the word 'pipeline' to indicate usage instructions.
    # We'll capture a small window around the match and check for 'pipeline'.
    start = max(script_mention.start() - 100, 0)
    end = script_mention.end() + 100
    snippet = content[start:end].lower()
    assert "pipeline" in snippet, (
        "README.md mentions 'run_all.py' but does not provide pipeline usage context. "
        "Include a brief description such as 'Run the full experiment pipeline via run_all.py'."
    )
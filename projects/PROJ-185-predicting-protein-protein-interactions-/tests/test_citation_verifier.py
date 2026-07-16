"""
Tests for the citation verification script (src/ci/validate_citations.py).

The test creates a temporary markdown file containing a known reachable URL
(https://example.com) and runs the validator against that temporary directory.
The validator should exit with code 0.
"""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def temp_md(tmp_path: Path) -> Path:
    """
    Create a simple markdown file with a single reachable URL.
    """
    md_file = tmp_path / "sample.md"
    md_file.write_text("Reference: https://example.com\n")
    return md_file


def test_validate_citations_success(temp_md: Path):
    """
    Run the citation validator on the temporary directory containing ``temp_md``.
    Expect a zero exit status.
    """
    # Resolve the script path relative to the repository root
    script_path = (
        Path(__file__).resolve().parents[2] / "src" / "ci" / "validate_citations.py"
    )
    result = subprocess.run(
        [sys.executable, str(script_path), "--path", str(temp_md.parent)],
        capture_output=True,
        text=True,
    )
    # Debug output in case of failure
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    assert result.returncode == 0, "Citation validator should succeed for reachable URLs"

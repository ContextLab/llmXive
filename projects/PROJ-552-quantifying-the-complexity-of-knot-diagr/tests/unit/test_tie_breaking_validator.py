"""
Unit test for the tie‑breaking validator (T030b).

The test creates a temporary ``tie_breaking_rules.md`` file with both valid and
invalid entries, invokes the validator programmatically, and checks that the
exit code matches the expectation.
"""

import sys
from pathlib import Path
from subprocess import run, PIPE

import pytest

# Import the validator's main function for direct testing
from reproducibility.tie_breaking_validator import main as validator_main


@pytest.fixture
def temp_rules_file(tmp_path: Path) -> Path:
    """
    Create a temporary ``tie_breaking_rules.md`` file in the repository root.
    The file contains a mix of correctly formatted and malformed lines.
    """
    rules_path = Path("docs/reproducibility/tie_breaking_rules.md")
    # Ensure the parent directory exists
    rules_path.parent.mkdir(parents=True, exist_ok=True)

    content = """\
# Tie‑breaking Rules
- braid_word: Prefer braid word representation over DT code.
- dt_code: Use DT code when braid word is unavailable.
- malformed rule without colon
- invalid key!: Keys may only contain alphanumerics, '_' or '-'.
"""
    rules_path.write_text(content, encoding="utf-8")
    yield rules_path
    # Cleanup after test
    if rules_path.is_file():
        rules_path.unlink()


def test_validator_exits_nonzero_on_malformed_rules(tmp_path, monkeypatch):
    """
    The validator should exit with a non‑zero status when malformed rules are
    present.
    """
    # Ensure the temporary file is used
    temp_rules_file(tmp_path)

    # Run the validator as a subprocess to capture the exit code
    result = run([sys.executable, "code/reproducibility/tie_breaking_validator.py"], stdout=PIPE, stderr=PIPE)
    assert result.returncode != 0, "Validator did not fail on malformed rules"


def test_validator_success_on_clean_rules(tmp_path, monkeypatch):
    """
    When all rules are well‑formed, the validator must exit with ``0``.
    """
    # Write a clean rules file
    clean_path = Path("docs/reproducibility/tie_breaking_rules.md")
    clean_path.parent.mkdir(parents=True, exist_ok=True)
    clean_path.write_text(
        "- braid_word: Prefer braid word representation over DT code.\n"
        "- dt_code: Use DT code when braid word is unavailable.\n",
        encoding="utf-8",
    )

    result = run([sys.executable, "code/reproducibility/tie_breaking_validator.py"], stdout=PIPE, stderr=PIPE)
    assert result.returncode == 0, f"Validator failed unexpectedly: {result.stderr.decode()}"
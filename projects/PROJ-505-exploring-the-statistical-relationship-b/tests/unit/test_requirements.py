"""
Basic sanity test for the requirements verification script.
Ensures that the script runs without raising and that the log file
contains the word \"success\" when the environment already satisfies
the pinned dependencies.
"""
import pytest
from pathlib import Path

from code.verify_requirements import main as verify_requirements

def test_verify_requirements_success(tmp_path, monkeypatch):
    # Run the verification script; it should not raise.
    verify_requirements()

    # The script writes a log file under results/requirements_install.log
    log_file = Path(__file__).parents[2] / "results" / "requirements_install.log"
    assert log_file.is_file()
    content = log_file.read_text()
    assert "success" in content.lower()
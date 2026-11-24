"""
Test suite for T001: Consolidate project layout, ensure no duplicate PT### entries,
verify imports and CLI help, and confirm quickstart command presence.
"""
import subprocess
import sys
from pathlib import Path
import re
from collections import Counter

import pytest


def test_run_audit_help():
    """
    Verify that the audit CLI module can be invoked with --help and exits with status 0.
    """
    # Construct the module command
    cmd = [sys.executable, "-m", "code.src.audit.run_audit", "--help"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    # The command should succeed
    assert result.returncode == 0, f"CLI help failed with return code {result.returncode}. Stderr: {result.stderr}"
    # Basic sanity: help output should contain usage information
    assert "usage" in result.stdout.lower() or "options" in result.stdout.lower()


def test_no_duplicate_pt_entries():
    """
    Scan all Python files under code/src/audit for PT### identifiers and ensure there are no duplicates.
    """
    audit_dir = Path("code/src/audit")
    pt_pattern = re.compile(r"PT\d{3}")
    found = []
    for py_file in audit_dir.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        found.extend(pt_pattern.findall(text))
    # Count occurrences
    counts = Counter(found)
    duplicates = [pt for pt, cnt in counts.items() if cnt > 1]
    assert not duplicates, f"Duplicate PT identifiers found: {duplicates}"


def test_quickstart_contains_command():
    """
    Ensure the quickstart guide contains the exact runnable command required by the spec.
    """
    quickstart_path = Path("specs/001-evaluating-the-statistical-validity-of-p/quickstart.md")
    assert quickstart_path.is_file(), f"Quickstart file not found at {quickstart_path}"
    content = quickstart_path.read_text(encoding="utf-8")
    expected_line = "python -m code.src.audit.run_audit data/input/urls.csv output/"
    # Look for the exact line (ignoring surrounding whitespace)
    lines = [line.strip() for line in content.splitlines()]
    assert expected_line in lines, f"Expected command not found in quickstart.md: '{expected_line}'"


# Optional: run all tests when this file is executed directly
if __name__ == "__main__":
    pytest.main([__file__])
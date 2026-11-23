"""
Tests for T031: Lintr Runner.
Verifies that the runner correctly identifies lint issues and TODOs.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import json

# Import the main logic if possible, or test via subprocess
# Since the runner is a standalone script, we test it via subprocess for integration
# and unit test the helper functions if they were separated. 
# For now, we test the behavior by creating a temporary project structure.

from code.lintr_runner import find_r_files, scan_todos, generate_report

def test_find_r_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "code").mkdir()
        (root / "code" / "test.R").touch()
        (root / "data").mkdir()
        (root / "data" / "data.R").touch()
        
        files = find_r_files(root / "code")
        assert len(files) == 1
        assert files[0].name == "test.R"

def test_scan_todos():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "test.R").write_text("# TODO: fix this\nx <- 1\n")
        
        todos = scan_todos(root)
        assert len(todos) == 1
        assert "TODO" in todos[0]["content"]

def test_generate_report_no_issues():
    lint_json = "[]"
    todos = []
    report = generate_report(lint_json, todos)
    assert "No linting errors found" in report
    assert "No TODOs" in report

def test_generate_report_with_critical():
    # Mock JSON for a cyclocomp issue
    mock_data = [
        {
            "file": "test.R",
            "line_number": 10,
            "column_number": 5,
            "type": "warning",
            "message": "Cyclomatic complexity is 12 (>= 10)",
            "linter": "cyclocomp_linter"
        }
    ]
    lint_json = json.dumps(mock_data)
    todos = []
    report = generate_report(lint_json, todos)
    assert "CRITICAL" in report
    assert "Complexity > 10" in report
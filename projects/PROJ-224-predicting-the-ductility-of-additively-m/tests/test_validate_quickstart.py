import os
import sys
import json
import tempfile
from pathlib import Path
import pytest

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.analysis.validate_quickstart import (
    parse_commands_from_markdown,
    check_file_exists,
    run_command,
    validate_quickstart
)

@pytest.fixture
def temp_quickstart_file(tmp_path):
    """Creates a temporary quickstart.md file with sample commands."""
    content = """
    # Quickstart Guide

    To run the pipeline:

    ```bash
    echo "Hello World"
    ```

    ```bash
    ls -la
    ```

    Check if data exists:
    ```bash
    test -f data/curated_builds.csv && echo "Found" || echo "Not Found"
    ```
    """
    file_path = tmp_path / "quickstart.md"
    file_path.write_text(content)
    return file_path

@pytest.fixture
def temp_project_structure(tmp_path):
    """Creates a temporary project structure with a data file."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "curated_builds.csv").write_text("col1,col2\n1,2\n")
    return tmp_path

def test_parse_commands_from_markdown(temp_quickstart_file):
    """Tests that commands are correctly extracted from markdown."""
    commands = parse_commands_from_markdown(temp_quickstart_file)
    assert len(commands) == 3
    assert "echo \"Hello World\"" in commands[0]
    assert "ls -la" in commands[1]
    assert "test -f data/curated_builds.csv" in commands[2]

def test_check_file_exists(temp_project_structure):
    """Tests file existence check."""
    assert check_file_exists("data/curated_builds.csv", temp_project_structure) is True
    assert check_file_exists("data/nonexistent.csv", temp_project_structure) is False

def test_run_command():
    """Tests command execution."""
    res = run_command("echo 'test'")
    assert res["success"] is True
    assert "test" in res["stdout"]
    assert res["return_code"] == 0

def test_run_command_timeout():
    """Tests command timeout handling."""
    res = run_command("sleep 5", timeout=1)
    assert res["success"] is False
    assert "Timeout" in res["stderr"]

def test_validate_quickstart_integration(temp_quickstart_file, temp_project_structure, monkeypatch):
    """
    Integration test for the full validation flow.
    We monkeypatch the cwd to our temp directory to ensure relative paths work.
    """
    # Change CWD to temp_project_structure
    monkeypatch.chdir(temp_project_structure)
    # Also copy the quickstart file there
    (temp_project_structure / "quickstart.md").write_text(temp_quickstart_file.read_text())

    result = validate_quickstart("quickstart.md")

    assert "status" in result
    assert "details" in result
    assert result["total_commands"] == 3

    # Check that the log file was created
    log_path = temp_project_structure / "data" / "quickstart_validation_log.json"
    assert log_path.exists()

    with open(log_path) as f:
        log_data = json.load(f)
    
    assert log_data["status"] == "passed" # All our dummy commands should pass
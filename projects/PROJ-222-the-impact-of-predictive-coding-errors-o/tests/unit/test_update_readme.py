"""
Unit tests for T013: update_readme.py
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the functions to test
# We need to mock config.get_data_dir and config.get_processed_dir
# to avoid needing the real project structure in tests.
from code.update_readme import (
    load_exclusion_log,
    parse_verified_datasets,
    generate_dataset_status_section,
    update_readme
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_load_exclusion_log_file_not_found(temp_dir):
    """Test loading exclusion log when file does not exist."""
    log_path = temp_dir / "nonexistent.json"
    result = load_exclusion_log(log_path)
    assert result == []


def test_load_exclusion_log_empty_file(temp_dir):
    """Test loading exclusion log from an empty file."""
    log_path = temp_dir / "empty.json"
    log_path.write_text("")
    result = load_exclusion_log(log_path)
    assert result == []


def test_load_exclusion_log_valid_json(temp_dir):
    """Test loading exclusion log with valid JSON."""
    log_path = temp_dir / "valid.json"
    data = [
        {"dataset_id": "openml_42277", "reason": "Missing columns"},
        {"dataset_id": "openml_42278", "reason": "Non-sequential"}
    ]
    log_path.write_text(json.dumps(data))
    result = load_exclusion_log(log_path)
    assert len(result) == 2
    assert result[0]["dataset_id"] == "openml_42277"


def test_parse_verified_datasets(temp_dir):
    """Test parsing verified datasets from README."""
    readme_path = temp_dir / "README.md"
    content = """
    # Data Directory

    ## Verified datasets
    - id: 42277
     source: openml
     type: time_perception
    - id: 42278
     source: openml
     type: time_perception

    ## Exclusion Logs
    """
    readme_path.write_text(content)
    result = parse_verified_datasets(readme_path)
    assert len(result) == 2
    assert "42277" in result
    assert result["42277"]["source"] == "openml"
    assert result["42277"]["type"] == "time_perception"


def test_generate_dataset_status_section(temp_dir):
    """Test generating the dataset status section."""
    verified = {
        "42277": {"id": "42277", "source": "openml", "type": "time_perception"},
        "42278": {"id": "42278", "source": "openml", "type": "time_perception"}
    }
    exclusion_log = [
        {"dataset_id": "openml_42277", "reason": "Missing columns"}
    ]

    section = generate_dataset_status_section(verified, exclusion_log)

    assert "### Dataset Status" not in section  # The function returns the content, not the header
    # Actually, the function returns the lines joined, let's check the content
    # The function returns the lines joined by newline.
    # Let's check the actual output format
    lines = section.split("\n")
    assert any("openml_42277: excluded (Missing columns)" in line for line in lines)
    assert any("openml_42278: valid" in line for line in lines)


def test_update_readme_replace_section(temp_dir):
    """Test updating README by replacing existing section."""
    readme_path = temp_dir / "README.md"
    initial_content = """
    # Data Directory

    ### Dataset Status
    - openml_42277: valid

    ## Other Section
    """
    readme_path.write_text(initial_content)

    new_status = "### Dataset Status\n- openml_42277: excluded (Test reason)\n- openml_42278: valid"

    update_readme(readme_path, new_status)

    updated_content = readme_path.read_text()
    assert "openml_42277: excluded (Test reason)" in updated_content
    assert "openml_42278: valid" in updated_content
    assert "Other Section" in updated_content


def test_update_readme_append_section(temp_dir):
    """Test updating README by appending section if not present."""
    readme_path = temp_dir / "README.md"
    initial_content = """
    # Data Directory

    ## Exclusion Logs
    Some text
    """
    readme_path.write_text(initial_content)

    new_status = "### Dataset Status\n- openml_42277: valid"

    update_readme(readme_path, new_status)

    updated_content = readme_path.read_text()
    assert "openml_42277: valid" in updated_content
    assert "## Exclusion Logs" in updated_content
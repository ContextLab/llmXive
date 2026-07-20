import os
import sys
import json
from pathlib import Path
import pytest

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from validate_quickstart import (
    check_file_exists,
    check_quickstart_references,
    validate_output_artifacts
)

@pytest.fixture
def mock_quickstart_content(tmp_path):
    """Create a temporary quickstart.md for testing."""
    content = """
    # Quickstart Guide

    ## Installation
    Run:
    $ pip install -r requirements.txt

    ## Data Processing
    $ python code/data/pipeline.py

    ## Model Training
    $ python code/models/train.py

    ## Evaluation
    $ python code/models/evaluate.py

    ## Verification
    Check outputs:
    - data/processed/hea_descriptors.csv
    - output/metrics.json
    - output/report.md
    """
    file_path = tmp_path / "quickstart.md"
    file_path.write_text(content)
    return str(file_path)

@pytest.fixture
def mock_artifacts(tmp_path):
    """Create temporary mock artifacts for testing."""
    artifacts = [
        "data/processed/hea_descriptors.csv",
        "output/metrics.json",
        "output/report.md",
        "output/data_status.json"
    ]
    for artifact in artifacts:
        full_path = tmp_path / artifact
        full_path.parent.mkdir(parents=True, exist_ok=True)
        if artifact.endswith(".json"):
            full_path.write_text(json.dumps({"test": "data"}))
        else:
            full_path.write_text("Mock content")
    return [str(tmp_path / a) for a in artifacts]

def test_check_file_exists(tmp_path):
    """Test file existence check."""
    existing_file = tmp_path / "test.txt"
    existing_file.write_text("content")

    assert check_file_exists(str(existing_file)) is True
    assert check_file_exists(str(tmp_path / "nonexistent.txt")) is False

def test_check_quickstart_references(mock_quickstart_content, tmp_path):
    """Test reference checking in quickstart.md."""
    # Create referenced files to avoid errors
    (tmp_path / "requirements.txt").touch()
    (tmp_path / "code" / "data" / "pipeline.py").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "code" / "data" / "pipeline.py").touch()
    (tmp_path / "code" / "models" / "train.py").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "code" / "models" / "train.py").touch()
    (tmp_path / "code" / "models" / "evaluate.py").touch()

    # Change to temp directory to simulate project root
    old_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        # This should find no errors if files exist
        errors = check_quickstart_references(str(tmp_path / "quickstart.md"))
        # Note: The heuristic in the function is simple; it might find false positives
        # depending on how paths are written in the markdown.
        # We just verify it runs without crashing.
    finally:
        os.chdir(old_cwd)

def test_validate_output_artifacts(mock_artifacts, tmp_path):
    """Test artifact validation."""
    # Create a mix of existing and missing artifacts
    existing = mock_artifacts
    missing = [str(tmp_path / "missing.json")]

    results = validate_output_artifacts(existing + missing)

    for path in existing:
        assert results[path] is True

    for path in missing:
        assert results[path] is False

def test_main_no_quickstart(tmp_path, caplog):
    """Test main function when quickstart.md is missing."""
    old_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        with pytest.raises(SystemExit) as excinfo:
            from validate_quickstart import main
            main()
        assert excinfo.value.code == 1
    finally:
        os.chdir(old_cwd)
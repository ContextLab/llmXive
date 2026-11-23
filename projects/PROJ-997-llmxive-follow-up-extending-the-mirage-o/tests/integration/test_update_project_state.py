import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest
import yaml
from datetime import datetime, timezone

from src.cli.update_project_state import compute_sha256, find_artifacts, update_project_state, main

@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create directory structure
        (root / "data" / "processed").mkdir(parents=True)
        (root / "data" / "models").mkdir(parents=True)
        (root / "docs" / "reports").mkdir(parents=True)
        (root / "state" / "projects").mkdir(parents=True)

        # Create dummy artifact files
        (root / "data" / "processed" / "training_sample.parquet").write_text("dummy parquet content")
        (root / "data" / "processed" / "test.json").write_text('{"key": "value"}')
        (root / "data" / "models" / "model.pkl").write_text("dummy pkl content")
        (root / "docs" / "reports" / "report.md").write_text("# Report Content")

        yield root

def test_compute_sha256():
    """Test SHA-256 computation on a known file."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test content")
        f_path = Path(f.name)

    try:
        hash_val = compute_sha256(f_path)
        # SHA-256 of "test content"
        expected = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
        assert hash_val == expected
    finally:
        f_path.unlink()

def test_compute_sha256_file_not_found():
    """Test that compute_sha256 raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        compute_sha256(Path("/nonexistent/file.txt"))

def test_find_artifacts(temp_project_root):
    """Test artifact discovery with glob patterns."""
    patterns = [
        "data/processed/*.parquet",
        "data/models/*.pkl",
        "data/processed/*.json",
        "docs/reports/*.md"
    ]

    artifacts = find_artifacts(patterns, temp_project_root)

    assert len(artifacts) == 4
    assert any("training_sample.parquet" in str(a) for a in artifacts)
    assert any("model.pkl" in str(a) for a in artifacts)
    assert any("test.json" in str(a) for a in artifacts)
    assert any("report.md" in str(a) for a in artifacts)

def test_update_project_state(temp_project_root):
    """Test full update_project_state workflow."""
    state_file = "state.yaml"
    project_id = "TEST-001"

    result = update_project_state(
        project_root=temp_project_root,
        project_id=project_id,
        state_file_name=state_file
    )

    assert result is True

    # Verify state file was created and updated
    state_path = temp_project_root / state_file
    assert state_path.exists()

    with open(state_path, "r") as f:
        state_data = yaml.safe_load(f)

    assert state_data["project_id"] == project_id
    assert "updated_at" in state_data
    assert "artifact_hashes" in state_data
    assert len(state_data["artifact_hashes"]) > 0

    # Verify timestamp format (ISO 8601)
    timestamp = state_data["updated_at"]
    assert isinstance(timestamp, str)
    # Try parsing to ensure valid ISO format
    datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

def test_main_success(temp_project_root, capsys):
    """Test main() function execution."""
    # Change to temp directory to avoid side effects
    original_cwd = Path.cwd()
    os.chdir(temp_project_root)

    try:
        with patch('sys.argv', ['update_project_state', '--project-root', str(temp_project_root)]):
            main()

        captured = capsys.readouterr()
        assert "Project state updated successfully" in captured.out

        # Verify state file exists
        state_path = temp_project_root / "state.yaml"
        assert state_path.exists()
    finally:
        os.chdir(original_cwd)

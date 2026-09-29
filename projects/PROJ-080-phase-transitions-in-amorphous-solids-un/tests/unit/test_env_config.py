import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Adjust import based on project structure if needed, assuming code/ is in path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from env_config import (
    check_environment_variable,
    get_cache_dir,
    get_dataset_path,
    verify_source_integrity,
    load_verified_dataset,
    DATASET_ID,
    RAW_DATA_DIR
)

def test_check_environment_variable_set():
    with patch.dict(os.environ, {"TEST_VAR": "value"}):
        assert check_environment_variable("TEST_VAR") is True

def test_check_environment_variable_unset():
    with patch.dict(os.environ, {}, clear=False):
        # Ensure the var is not set
        if "TEST_VAR_NOT_SET" in os.environ:
            del os.environ["TEST_VAR_NOT_SET"]
        assert check_environment_variable("TEST_VAR_NOT_SET") is False

def test_get_cache_dir_creates_directory():
    # Mock a temporary path to avoid cluttering
    with patch("env_config.PROJECT_ROOT", Path("/tmp/test_proj")):
        with patch("env_config.Path.mkdir") as mock_mkdir:
            result = get_cache_dir()
            mock_mkdir.assert_called_once()
            assert result == Path("/tmp/test_proj/data/cache")

def test_get_dataset_path():
    expected = RAW_DATA_DIR / DATASET_ID
    assert get_dataset_path() == expected

def test_verify_source_integrity_missing_manifest(tmp_path):
    # Create a temp directory without manifest
    result = verify_source_integrity(tmp_path, "fake_checksum")
    assert result is False

def test_verify_source_integrity_mismatch(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"checksum": "wrong"}')
    result = verify_source_integrity(tmp_path, "correct")
    assert result is False

def test_load_verified_dataset_success():
    # Mock the load_dataset function
    mock_ds = MagicMock()
    mock_ds.train = []
    with patch("env_config.load_dataset", return_value=mock_ds):
        result = load_verified_dataset()
        assert result is not None

def test_load_verified_dataset_failure():
    with patch("env_config.load_dataset", side_effect=Exception("Connection Error")):
        with pytest.raises(RuntimeError, match="Data fetch failed"):
            load_verified_dataset()

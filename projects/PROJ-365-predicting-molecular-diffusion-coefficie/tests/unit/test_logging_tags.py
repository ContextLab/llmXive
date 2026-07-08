import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.logging import (
    log_missing_data_excluded,
    log_invalid_smiles,
    get_log_file_path,
    get_logger,
    MISSING_DATA_TAG,
    ERROR_SMILES_TAG
)
from utils.config import get_project_root, get_log_path

@pytest.fixture
def setup_test_env():
    """
    Sets up a temporary directory structure to mimic the project environment
    for testing logging functionality without polluting the real project state.
    """
    # Create a temporary directory to act as the project root for this test
    temp_root = Path(tempfile.mkdtemp())

    # Create necessary subdirectories
    data_dir = temp_root / "data"
    logs_dir = data_dir / "logs"
    logs_dir.mkdir(parents=True)

    # Mock the config to return our temp paths
    # We need to patch the config module's behavior
    original_get_project_root = None
    original_get_log_path = None

    # Store original functions if they exist
    import utils.config as config_module
    if hasattr(config_module, '_cached_root'):
        original_get_project_root = config_module._cached_root
    if hasattr(config_module, '_cached_log_path'):
        original_get_log_path = config_module._cached_log_path

    # Override config functions temporarily
    def mock_get_project_root():
        return temp_root

    def mock_get_log_path():
        return logs_dir / "ingestion.log"

    config_module.get_project_root = mock_get_project_root
    config_module.get_log_path = mock_get_log_path

    # Reset logger to force re-initialization with new path
    import utils.logging as logging_module
    logging_module._logger = None
    logging_module._log_file_path = None

    yield temp_root

    # Cleanup
    shutil.rmtree(temp_root, ignore_errors=True)

    # Restore original config if they existed
    if original_get_project_root:
        config_module._cached_root = original_get_project_root
        config_module.get_project_root = lambda: original_get_project_root
    if original_get_log_path:
        config_module._cached_log_path = original_get_log_path
        config_module.get_log_path = lambda: original_get_log_path

    # Reset logger again
    logging_module._logger = None
    logging_module._log_file_path = None

def test_logging_tags_appear_in_log(setup_test_env):
    """
    Asserts that the tags [MISSING_DATA_EXCLUDED] and [ERROR_SMILES] appear
    in data/logs/ingestion.log after processing a mixed-validity scenario.
    """
    temp_root = setup_test_env

    # Get the log file path
    log_file = get_log_file_path()

    # Ensure the file exists (logger init creates it)
    # We need to trigger init first
    get_logger()

    # Clear the log file content for a clean test
    if log_file.exists():
        log_file.write_text("")

    # Simulate logging missing data
    log_missing_data_excluded("row_123", "Missing solvent viscosity")

    # Simulate logging invalid SMILES
    log_invalid_smiles("row_456", "C12C3C4C5C6C7C8C9C10C11C1C2C3C4C5C6C7C8C9C10C11", "Syntax error in ring closure")

    # Simulate a few more entries to ensure robustness
    log_missing_data_excluded("row_789")
    log_invalid_smiles("row_999", "INVALID_SMILES_STRING", "Unknown atom type")

    # Read the log file content
    content = log_file.read_text()

    # Assert that the specific tags appear in the log
    assert MISSING_DATA_TAG in content, f"Tag '{MISSING_DATA_TAG}' not found in log file. Content: {content}"
    assert ERROR_SMILES_TAG in content, f"Tag '{ERROR_SMILES_TAG}' not found in log file. Content: {content}"

    # Verify that the log contains the expected structure
    lines = content.strip().split('\n')
    assert len(lines) >= 4, "Expected at least 4 log entries"

    # Verify timestamps are present (basic check for YYYY-MM-DD format)
    for line in lines:
        assert len(line) > 20, f"Log line seems too short to contain timestamp: {line}"
        # Basic check that it starts with a date-like string
        assert line[4] == '-', f"Timestamp format incorrect in line: {line}"
        assert line[7] == ':', f"Timestamp format incorrect in line: {line}"

def test_log_content_format(setup_test_env):
    """
    Verifies that the log content includes the record ID and reason/error message.
    """
    temp_root = setup_test_env
    log_file = get_log_file_path()
    get_logger() # Init
    log_file.write_text("") # Clear log

    test_id = "TEST_RECORD_001"
    test_reason = "Specific reason for exclusion"

    log_missing_data_excluded(test_id, test_reason)

    content = log_file.read_text()

    assert test_id in content, f"Record ID {test_id} not found in log"
    assert test_reason in content, f"Reason {test_reason} not found in log"
    assert MISSING_DATA_TAG in content, f"Tag {MISSING_DATA_TAG} not found"

def test_log_invalid_smiles_content(setup_test_env):
    """
    Verifies that the log content for invalid SMILES includes the SMILES string (truncated if needed).
    """
    temp_root = setup_test_env
    log_file = get_log_file_path()
    get_logger() # Init
    log_file.write_text("")

    test_id = "SMILES_TEST_001"
    test_smiles = "CCCCC"
    test_error = "Valence error"

    log_invalid_smiles(test_id, test_smiles, test_error)

    content = log_file.read_text()

    assert test_id in content, f"Record ID {test_id} not found"
    assert test_smiles in content, f"SMILES {test_smiles} not found"
    assert test_error in content, f"Error {test_error} not found"
    assert ERROR_SMILES_TAG in content, f"Tag {ERROR_SMILES_TAG} not found"
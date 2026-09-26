"""
Unit tests for the exclusion log initialization logic (T011d).
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.init_exclusion_log import initialize_exclusion_log
from config import DataConfig


@pytest.fixture
def temp_processed_dir(tmp_path):
    """Create a temporary directory to act as the processed data directory."""
    # We need to mock the DataConfig or temporarily change the config value.
    # Since DataConfig reads from env or defaults, we'll test the file creation
    # logic directly by passing a path or mocking the config.
    # For simplicity in this unit test, we will test the file creation logic
    # by calling the function and checking the result, assuming the default
    # config points to a place we can write or we override it.

    # Actually, initialize_exclusion_log uses DataConfig() directly.
    # To test properly without side effects on real project data,
    # we would ideally mock the config or run in a controlled env.
    # Here, we verify the file content logic by checking the file created
    # by the function if it runs against the default path, or we patch the path.

    # Let's patch the DataConfig to use a temp dir for this test.
    import data.init_exclusion_log as module_under_test

    original_config = module_under_test.DataConfig

    class MockDataConfig:
        processed_dir = str(tmp_path)

    module_under_test.DataConfig = MockDataConfig

    yield tmp_path

    # Restore
    module_under_test.DataConfig = original_config


def test_initialize_exclusion_log_creates_file(temp_processed_dir):
    """Test that the function creates the file with correct headers."""
    result_path = initialize_exclusion_log()

    assert result_path.exists(), "The exclusion log file was not created."
    assert result_path.name == "exclusion_raw.log", "The file name is incorrect."

    with open(result_path, 'r', encoding='utf-8') as f:
        content = f.read()

    assert content.startswith("row_index,reason,original_smiles"), "Headers are missing or incorrect."
    assert content.count('\n') == 1, "File should only contain the header line initially."


def test_initialize_exclusion_log_skips_if_exists(temp_processed_dir):
    """Test that the function does not overwrite an existing file."""
    # Create the file first
    result_path = initialize_exclusion_log()

    # Write some fake data to simulate existing content
    with open(result_path, 'w', encoding='utf-8') as f:
        f.write("row_index,reason,original_smiles\n1,test_reason,CCO\n")

    # Call again
    initialize_exclusion_log()

    # Verify content is unchanged
    with open(result_path, 'r', encoding='utf-8') as f:
        content = f.read()

    assert "1,test_reason,CCO" in content, "Existing data was overwritten."
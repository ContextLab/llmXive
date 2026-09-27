"""
Integration tests for the testing framework setup.
Ensures that unit tests, fixtures, and imports work together correctly.
"""
import pytest
from pathlib import Path
from config import get_path
from utils.logging_config import get_logger
from utils.state_manager import compute_file_hash

def test_integration_import_chain(test_data_dir):
    """
    Integration test verifying that config, logging, and state manager
    can be imported and used together in a test context.
    """
    # 1. Verify config works
    data_path = get_path("data")
    assert data_path.exists()

    # 2. Verify logging works
    logger = get_logger("integration_test")
    logger.info("Integration test started")
    assert logger is not None

    # 3. Verify state manager works with real file
    test_file = test_data_dir / "integration_test_file.txt"
    test_file.write_text("Integration test content")
    
    file_hash = compute_file_hash(test_file)
    assert file_hash is not None
    assert len(file_hash) == 64

def test_fixture_injection(test_output_dir, temp_state_dir):
    """
    Integration test verifying that pytest fixtures (test_output_dir, temp_state_dir)
    are correctly injected and usable.
    """
    assert test_output_dir.exists()
    assert temp_state_dir.exists()
    
    # Create a file in output dir
    output_file = test_output_dir / "test_output.txt"
    output_file.write_text("Output")
    assert output_file.exists()
    
    # Create a file in temp state dir
    state_file = temp_state_dir / "test_state.yaml"
    state_file.write_text("state: true")
    assert state_file.exists()

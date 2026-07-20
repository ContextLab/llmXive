"""
Basic smoke test to verify pytest configuration and environment setup.
This test ensures that the project structure and imports are working correctly.
"""
import os
import sys
from pathlib import Path

def test_project_root_is_accessible():
    """Verify that we can access the project root structure."""
    current_dir = Path(__file__).parent
    code_dir = current_dir.parent
    project_root = code_dir.parent

    assert project_root.exists(), f"Project root {project_root} does not exist"
    assert (project_root / "code").exists(), "code directory missing"
    assert (project_root / "data").exists(), "data directory missing"

def test_utils_module_importable():
    """Verify that the utils module can be imported."""
    try:
        from utils import (
            get_project_root_path,
            get_code_path,
            get_data_path,
            setup_logger,
            get_logger
        )
        assert callable(get_project_root_path)
        assert callable(get_code_path)
        assert callable(get_data_path)
        assert callable(setup_logger)
    except ImportError as e:
        pytest.fail(f"Failed to import utils module: {e}")

def test_config_module_importable():
    """Verify that the config module can be imported."""
    try:
        from config import (
            get_project_root,
            get_data_dir,
            ensure_data_dirs,
            load_dataset_urls
        )
        assert callable(get_project_root)
        assert callable(get_data_dir)
    except ImportError as e:
        pytest.fail(f"Failed to import config module: {e}")

def test_schemas_module_importable():
    """Verify that the schemas module can be imported."""
    try:
        from schemas import MicrobialTaxa, CognitiveScore
        assert MicrobialTaxa is not None
        assert CognitiveScore is not None
    except ImportError as e:
        pytest.fail(f"Failed to import schemas module: {e}")

def test_data_directories_exist():
    """Verify that required data directories exist."""
    from utils import get_data_raw_path, get_data_processed_path, get_data_qc_path

    raw_dir = get_data_raw_path()
    processed_dir = get_data_processed_path()
    qc_dir = get_data_qc_path()

    assert raw_dir.exists(), f"Raw data directory missing: {raw_dir}"
    assert processed_dir.exists(), f"Processed data directory missing: {processed_dir}"
    assert qc_dir.exists(), f"QC data directory missing: {qc_dir}"

def test_logging_functionality(mock_logger):
    """Test that logging works correctly."""
    logger, log_file = mock_logger
    
    logger.info("Test log message")
    logger.debug("Debug message")
    logger.warning("Warning message")
    
    # Verify log file exists and contains messages
    assert log_file.exists(), "Log file was not created"
    
    content = log_file.read_text()
    assert "Test log message" in content
    assert "Warning message" in content
    assert "DEBUG" in content or "debug" in content.lower()
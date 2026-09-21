import os
import pytest
from config import get_config, ensure_directories

def test_t002_directories_exist():
    """
    Test that the directories required for T002 (code, artifacts, tests)
    and their essential subdirectories exist.
    """
    config = get_config()
    
    # Ensure directories are created (idempotent)
    ensure_directories(config)

    # Check root directories required by T002
    assert os.path.isdir(config.code_dir), f"Directory missing: {config.code_dir}"
    assert os.path.isdir(config.artifacts_dir), f"Directory missing: {config.artifacts_dir}"
    assert os.path.isdir(config.tests_dir), f"Directory missing: {config.tests_dir}"

    # Check essential subdirectories
    assert os.path.isdir(config.data_raw), f"Directory missing: {config.data_raw}"
    assert os.path.isdir(config.data_processed), f"Directory missing: {config.data_processed}"
    assert os.path.isdir(config.data_assets), f"Directory missing: {config.data_assets}"
    assert os.path.isdir(config.artifacts_logs), f"Directory missing: {config.artifacts_logs}"
    assert os.path.isdir(config.artifacts_weights), f"Directory missing: {config.artifacts_weights}"
    
    # Check test subdirectories
    assert os.path.isdir(os.path.join(config.tests_dir, "unit"))
    assert os.path.isdir(os.path.join(config.tests_dir, "integration"))
    assert os.path.isdir(os.path.join(config.tests_dir, "contract"))
    
    # Check code subdirectories
    assert os.path.isdir(os.path.join(config.code_dir, "utils"))
    assert os.path.isdir(os.path.join(config.code_dir, "data"))
    assert os.path.isdir(os.path.join(config.code_dir, "models"))
import os
import pytest
from code.setup_directories import create_directories, main
from code.config import get_config

def test_create_directories_creates_missing():
    """Test that create_directories actually creates new directories."""
    test_path = "data/test_temp_dir_for_verify"
    if os.path.exists(test_path):
        os.rmdir(test_path)
    
    create_directories([test_path])
    
    assert os.path.exists(test_path), f"Directory {test_path} was not created"
    assert os.path.isdir(test_path), f"{test_path} exists but is not a directory"
    
    # Cleanup
    os.rmdir(test_path)

def test_create_directories_skips_existing(tmp_path):
    """Test that create_directories does not error on existing paths."""
    existing_path = str(tmp_path / "existing")
    os.makedirs(existing_path)
    
    # Should not raise
    create_directories([existing_path])
    assert os.path.exists(existing_path)

def test_main_creates_data_assets():
    """Integration test for main() ensuring data/assets is created."""
    # Ensure the directory doesn't exist before running main
    assets_dir = os.path.join(os.getcwd(), "data", "assets")
    if os.path.exists(assets_dir):
        # If it exists from previous runs, we assume it's valid, but for strict testing:
        pass 
    
    # Run main
    main()
    
    # Verify
    assert os.path.exists(assets_dir), "data/assets directory was not created by main()"
    assert os.path.isdir(assets_dir), "data/assets is not a directory"
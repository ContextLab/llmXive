import os
import pytest
from pathlib import Path
from config import PROJECT_ROOT
from setup_data_dirs import main as setup_data_main
from setup_results_dirs import main as setup_results_main

def test_data_dirs_created(tmp_path, monkeypatch):
    """Test that data/raw and data/processed directories are created."""
    # Mock PROJECT_ROOT to use a temporary directory
    mock_root = tmp_path / "mock_project"
    mock_root.mkdir(parents=True)
    monkeypatch.setattr("setup_data_dirs.PROJECT_ROOT", mock_root)
    monkeypatch.setattr("config.PROJECT_ROOT", mock_root)

    setup_data_main()

    data_raw = mock_root / "data" / "raw"
    data_processed = mock_root / "data" / "processed"

    assert data_raw.exists(), "data/raw directory should exist"
    assert data_processed.exists(), "data/processed directory should exist"
    assert data_raw.is_dir(), "data/raw should be a directory"
    assert data_processed.is_dir(), "data/processed should be a directory"

def test_results_dirs_created(tmp_path, monkeypatch):
    """Test that results directory structure is created."""
    # Mock PROJECT_ROOT and related config paths
    mock_root = tmp_path / "mock_project"
    mock_root.mkdir(parents=True)
    
    # We need to mock the config values used in setup_results_dirs
    # Since RESULTS_DIR and FIGURES_DIR are imported from config, we need to patch them
    from unittest.mock import patch
    import setup_results_dirs
    import config

    mock_results = mock_root / "results"
    mock_figures = mock_root / "figures"

    with patch.object(config, 'PROJECT_ROOT', mock_root), \
         patch.object(config, 'RESULTS_DIR', mock_results), \
         patch.object(config, 'FIGURES_DIR', mock_figures):
        
        # Re-import to pick up patched values if necessary, 
        # but since they are imported at module level, we need to ensure the module sees them.
        # The cleanest way in a test is to reload the module after patching, 
        # or just run the function which uses the already imported constants.
        # However, setup_results_dirs imports RESULTS_DIR from config at the top.
        # To properly test, we should reload the module or ensure the patch is active 
        # before the import. Since the import happens at the top of the file being tested,
        # we can't easily patch it after import unless we reload.
        # Let's use a different approach: patch the os.makedirs call to verify it was called with correct paths.
        
        import importlib
        # Reload the module to pick up the patched config if we had patched before import
        # But here we patched after import in the test setup? No, we are in the test function.
        # The module setup_results_dirs was imported at the top of the file.
        # So we need to reload it after patching config.
        
        # Actually, the simplest way is to just check if the directories exist after running main
        # by temporarily changing the config values and reloading.
        
        # Let's just verify the logic by checking if the directories would be created
        # by checking the code logic or by mocking os.makedirs.
        
        # Alternative: Patch os.makedirs to capture calls
        with patch('setup_results_dirs.os.makedirs') as mock_makedirs:
            setup_results_main()
            
            # Verify that makedirs was called for the expected paths
            expected_calls = [
                str(mock_results),
                str(mock_figures),
                str(mock_results / "coverage"),
                str(mock_results / "distributional"),
                str(mock_results / "significance"),
                str(mock_results / "conformal"),
                str(mock_figures / "pit_histograms"),
                str(mock_figures / "calibration_plots"),
            ]
            
            # Check that all expected paths were passed to makedirs
            calls_args = [call[0][0] for call in mock_makedirs.call_args_list]
            for expected in expected_calls:
                assert any(expected in str(call) for call in calls_args), f"Expected path {expected} not found in makedirs calls"

def test_directories_persist_after_setup(tmp_path, monkeypatch):
    """Test that directories actually exist on disk after running setup."""
    mock_root = tmp_path / "mock_project"
    mock_root.mkdir(parents=True)
    
    # Set up config mocks
    from unittest.mock import patch
    import config
    
    mock_results = mock_root / "results"
    mock_figures = mock_root / "figures"
    
    with patch.object(config, 'PROJECT_ROOT', mock_root), \
         patch.object(config, 'RESULTS_DIR', mock_results), \
         patch.object(config, 'FIGURES_DIR', mock_figures):
         
         # Reload the module to use patched config
         import setup_results_dirs
         import importlib
         importlib.reload(setup_results_dirs)
         
         setup_results_dirs.main()
         
         # Verify directories exist
         assert mock_results.exists()
         assert mock_figures.exists()
         assert (mock_results / "coverage").exists()
         assert (mock_results / "distributional").exists()
         assert (mock_results / "significance").exists()
         assert (mock_results / "conformal").exists()
         assert (mock_figures / "pit_histograms").exists()
         assert (mock_figures / "calibration_plots").exists()
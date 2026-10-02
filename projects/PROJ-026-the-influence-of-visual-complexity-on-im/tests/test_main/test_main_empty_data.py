"""
Test for T045: Validation of empty complexity scores in main.py.
"""
import pytest
import pandas as pd
import os
import sys
from pathlib import Path
import tempfile
import shutil

# We need to mock the environment to test the validation logic without running the full pipeline
# Since main.py exits via sys.exit(1), we catch SystemExit.

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary directory structure mimicking the project."""
    # Create necessary directories
    data_processed = tmp_path / "data" / "processed"
    data_processed.mkdir(parents=True)
    
    # Create a mock amendment file so T000 check passes
    specs_dir = tmp_path / "specs" / "001-the-influence-of-visual-complexity-on-im"
    specs_dir.mkdir(parents=True)
    (specs_dir / "amendment-001.md").write_text("# Amendment\nStatus: Ratified")

    return tmp_path

def test_main_raises_on_empty_complexity_csv(temp_project_root, monkeypatch):
    """
    Test that main.py raises SystemExit (simulating ValueError/Abort) 
    when complexity_scores.csv is empty.
    """
    # Create an empty CSV
    csv_path = temp_project_root / "data" / "processed" / "complexity_scores.csv"
    csv_path.write_text("filename,edge_density,entropy,fractal_dim,complexity_category\n")
    
    # Mock the get_project_root to return our temp dir
    from config import get_project_root
    monkeypatch.setattr("config.get_project_root", lambda: temp_project_root)
    
    # We also need to mock the other imports in main.py to prevent actual execution
    # We will import main and patch the specific functions it calls
    import code.main as main_module
    
    # Mock the subsequent steps to ensure we hit the validation and then stop
    # The validation happens before run_pca_main, etc.
    
    # Run main and expect SystemExit
    with pytest.raises(SystemExit) as exc_info:
        # We need to simulate the args parsing as well
        # But since we are testing the logic inside main(), we can just call main()
        # after patching the necessary dependencies to avoid side effects
        
        # Patch the setup_logging to avoid file writes
        monkeypatch.setattr("code.main.setup_logging", lambda: type('Logger', (), {'info': lambda s, m: None, 'error': lambda s, m: None})())
        
        # Patch ensure_directories
        monkeypatch.setattr("code.main.ensure_directories", lambda: None)
        
        # We need to patch the imports of the sub-modules to avoid them running
        # But the validation logic is inline in main(), so we just need to ensure
        # the code reaches that point.
        
        # Since main() calls run_stimuli_main() etc, we must mock those to avoid errors
        # The validation is BEFORE run_pca_main, but AFTER run_stimuli_main and run_process_main.
        # To test the validation specifically, we need to mock the preceding steps to succeed.
        
        monkeypatch.setattr("code.main.run_stimuli_main", lambda: None)
        monkeypatch.setattr("code.main.run_counterbalance_main", lambda: None)
        monkeypatch.setattr("code.main.run_load_main", lambda **kwargs: None)
        monkeypatch.setattr("code.main.run_process_main", lambda: None)
        monkeypatch.setattr("code.main.run_pca_main", lambda: None)
        
        # Mock args
        class Args:
            skip_stimuli = True
            skip_analysis = False
            null_effect = False
        
        monkeypatch.setattr("code.main.parse_args", lambda: Args())
        
        main_module.main()
    
    assert exc_info.value.code == 1

def test_main_raises_on_all_skipped(temp_project_root, monkeypatch):
    """
    Test that main.py raises SystemExit when all rows in complexity_scores.csv are 'skipped'.
    """
    # Create a CSV with only skipped rows
    csv_path = temp_project_root / "data" / "processed" / "complexity_scores.csv"
    csv_path.write_text("filename,edge_density,entropy,fractal_dim,complexity_category\nimg1.jpg,0.1,0.2,0.3,skipped\nimg2.jpg,0.1,0.2,0.3,skipped\n")
    
    # Mock environment
    from config import get_project_root
    monkeypatch.setattr("config.get_project_root", lambda: temp_project_root)
    
    import code.main as main_module
    
    # Mock dependencies
    monkeypatch.setattr("code.main.setup_logging", lambda: type('Logger', (), {'info': lambda s, m: None, 'error': lambda s, m: None})())
    monkeypatch.setattr("code.main.ensure_directories", lambda: None)
    monkeypatch.setattr("code.main.run_stimuli_main", lambda: None)
    monkeypatch.setattr("code.main.run_counterbalance_main", lambda: None)
    monkeypatch.setattr("code.main.run_load_main", lambda **kwargs: None)
    monkeypatch.setattr("code.main.run_process_main", lambda: None)
    monkeypatch.setattr("code.main.run_pca_main", lambda: None)
    
    class Args:
        skip_stimuli = True
        skip_analysis = False
        null_effect = False
    
    monkeypatch.setattr("code.main.parse_args", lambda: Args())
    
    with pytest.raises(SystemExit) as exc_info:
        main_module.main()
    
    assert exc_info.value.code == 1

def test_main_passes_on_valid_data(temp_project_root, monkeypatch):
    """
    Test that main.py proceeds when valid data exists.
    """
    # Create a valid CSV
    csv_path = temp_project_root / "data" / "processed" / "complexity_scores.csv"
    csv_path.write_text("filename,edge_density,entropy,fractal_dim,complexity_category\nimg1.jpg,0.1,0.2,0.3,Low\nimg2.jpg,0.5,0.6,0.7,High\n")
    
    # Mock environment
    from config import get_project_root
    monkeypatch.setattr("config.get_project_root", lambda: temp_project_root)
    
    import code.main as main_module
    
    # Mock dependencies
    mock_logger = type('Logger', (), {'info': lambda s, m: None, 'error': lambda s, m: None})()
    monkeypatch.setattr("code.main.setup_logging", lambda: mock_logger)
    monkeypatch.setattr("code.main.ensure_directories", lambda: None)
    monkeypatch.setattr("code.main.run_stimuli_main", lambda: None)
    monkeypatch.setattr("code.main.run_counterbalance_main", lambda: None)
    monkeypatch.setattr("code.main.run_load_main", lambda **kwargs: None)
    monkeypatch.setattr("code.main.run_process_main", lambda: None)
    monkeypatch.setattr("code.main.run_pca_main", lambda: None)
    monkeypatch.setattr("code.main.run_permutation_main", lambda: None)
    monkeypatch.setattr("code.main.run_sensitivity_main", lambda: None)
    monkeypatch.setattr("code.main.run_results_main", lambda: None)
    
    class Args:
        skip_stimuli = True
        skip_analysis = False
        null_effect = False
    
    monkeypatch.setattr("code.main.parse_args", lambda: Args())
    
    # Should NOT raise
    try:
        main_module.main()
    except SystemExit:
        pytest.fail("main() raised SystemExit unexpectedly on valid data")
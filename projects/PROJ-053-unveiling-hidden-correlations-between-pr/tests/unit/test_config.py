import os
import pytest
from pathlib import Path

def test_config_paths():
    """Test that config returns valid paths."""
    from code.config import (
        get_project_root,
        get_raw_data_dir,
        get_processed_data_dir,
        get_results_dir,
        get_models_dir,
        get_figures_dir,
        get_docs_dir,
        get_state_dir,
        get_logs_dir,
        get_contracts_dir,
        ensure_directories
    )
    
    root = get_project_root()
    assert isinstance(root, Path)
    assert root.exists()
    
    ensure_directories()
    
    assert get_raw_data_dir().exists()
    assert get_processed_data_dir().exists()
    assert get_results_dir().exists()
    assert get_models_dir().exists()
    assert get_figures_dir().exists()
    assert get_docs_dir().exists()
    assert get_state_dir().exists()
    assert get_logs_dir().exists()
    assert get_contracts_dir().exists()

def test_random_seed():
    """Test random seed retrieval."""
    from code.config import get_random_seed
    assert isinstance(get_random_seed(), int)
    assert get_random_seed() == 42

def test_time_limit():
    """Test time limit configuration."""
    from code.config import get_time_limit_seconds
    assert get_time_limit_seconds() == 21600

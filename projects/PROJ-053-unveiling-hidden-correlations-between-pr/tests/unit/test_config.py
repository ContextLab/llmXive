import pytest
import os
import tempfile
from pathlib import Path

# Import from the project's config module
from config import (
    get_project_root,
    get_data_dir,
    get_raw_data_dir,
    get_processed_data_dir,
    get_results_dir,
    get_models_dir,
    get_figures_dir,
    get_docs_dir,
    get_state_dir,
    get_logs_dir,
    get_random_seed,
    get_time_limit_seconds,
    ensure_directories
)

def test_get_project_root():
    """Test getting project root directory."""
    root = get_project_root()
    
    assert root is not None
    assert isinstance(root, Path)
    assert root.exists()

def test_get_data_dir():
    """Test getting data directory."""
    data_dir = get_data_dir()
    
    assert data_dir is not None
    assert isinstance(data_dir, Path)
    # Data dir should be under project root
    assert str(data_dir).startswith(str(get_project_root()))

def test_get_raw_data_dir():
    """Test getting raw data directory."""
    raw_dir = get_raw_data_dir()
    
    assert raw_dir is not None
    assert isinstance(raw_dir, Path)

def test_get_processed_data_dir():
    """Test getting processed data directory."""
    processed_dir = get_processed_data_dir()
    
    assert processed_dir is not None
    assert isinstance(processed_dir, Path)

def test_get_results_dir():
    """Test getting results directory."""
    results_dir = get_results_dir()
    
    assert results_dir is not None
    assert isinstance(results_dir, Path)

def test_get_models_dir():
    """Test getting models directory."""
    models_dir = get_models_dir()
    
    assert models_dir is not None
    assert isinstance(models_dir, Path)

def test_get_figures_dir():
    """Test getting figures directory."""
    figures_dir = get_figures_dir()
    
    assert figures_dir is not None
    assert isinstance(figures_dir, Path)

def test_get_docs_dir():
    """Test getting docs directory."""
    docs_dir = get_docs_dir()
    
    assert docs_dir is not None
    assert isinstance(docs_dir, Path)

def test_get_state_dir():
    """Test getting state directory."""
    state_dir = get_state_dir()
    
    assert state_dir is not None
    assert isinstance(state_dir, Path)

def test_get_logs_dir():
    """Test getting logs directory."""
    logs_dir = get_logs_dir()
    
    assert logs_dir is not None
    assert isinstance(logs_dir, Path)

def test_get_random_seed():
    """Test getting random seed."""
    seed = get_random_seed()
    
    assert seed is not None
    assert isinstance(seed, int)

def test_get_time_limit_seconds():
    """Test getting time limit in seconds."""
    time_limit = get_time_limit_seconds()
    
    assert time_limit is not None
    assert isinstance(time_limit, int)
    assert time_limit > 0

def test_ensure_directories():
    """Test directory creation."""
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        # Temporarily override the project root
        import config
        original_root = config.PROJECT_ROOT
        config.PROJECT_ROOT = Path(tmpdir)
        
        try:
            ensure_directories()
            
            # Verify directories were created
            assert (Path(tmpdir) / 'data').exists()
            assert (Path(tmpdir) / 'data' / 'raw').exists()
            assert (Path(tmpdir) / 'data' / 'processed').exists()
            assert (Path(tmpdir) / 'results').exists()
            assert (Path(tmpdir) / 'results' / 'models').exists()
            assert (Path(tmpdir) / 'figures').exists()
            assert (Path(tmpdir) / 'docs').exists()
            assert (Path(tmpdir) / 'state').exists()
            assert (Path(tmpdir) / 'logs').exists()
        finally:
            config.PROJECT_ROOT = original_root

def test_directories_exist_after_ensure():
    """Test that directories exist after ensure_directories is called."""
    ensure_directories()
    
    # Verify main directories exist
    assert get_data_dir().exists()
    assert get_raw_data_dir().exists()
    assert get_processed_data_dir().exists()
    assert get_results_dir().exists()
    assert get_models_dir().exists()
    assert get_figures_dir().exists()
    assert get_docs_dir().exists()
    assert get_state_dir().exists()
    assert get_logs_dir().exists()
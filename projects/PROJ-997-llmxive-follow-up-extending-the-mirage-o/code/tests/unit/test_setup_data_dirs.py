import os
import pytest
from pathlib import Path
import tempfile
import shutil
from scripts.setup_data_dirs import setup_data_directories, create_init_files

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as the project root."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_setup_data_directories_creates_folders(temp_project_root):
    """Test that setup_data_directories creates the required folders."""
    setup_data_directories(str(temp_project_root))
    
    data_path = temp_project_root / "data"
    assert data_path.exists()
    assert data_path.is_dir()
    
    raw_dir = data_path / "raw"
    processed_dir = data_path / "processed"
    models_dir = data_path / "models"
    
    assert raw_dir.exists()
    assert processed_dir.exists()
    assert models_dir.exists()
    
    assert raw_dir.is_dir()
    assert processed_dir.is_dir()
    assert models_dir.is_dir()

def test_create_init_files_creates_init(temp_project_root):
    """Test that create_init_files creates __init__.py in data subdirectories."""
    # First setup directories
    setup_data_directories(str(temp_project_root))
    # Then create init files
    create_init_files(str(temp_project_root))
    
    data_path = temp_project_root / "data"
    init_file = data_path / "__init__.py"
    
    sub_dirs = ["raw", "processed", "models"]
    for sub_dir in sub_dirs:
        sub_path = data_path / sub_dir
        sub_init = sub_path / "__init__.py"
        assert sub_init.exists()
        assert sub_init.is_file()

def test_full_workflow(temp_project_root):
    """Test the full workflow of setting up directories and init files."""
    # Run main logic
    setup_data_directories(str(temp_project_root))
    create_init_files(str(temp_project_root))
    
    # Verify structure
    data_path = temp_project_root / "data"
    assert (data_path / "__init__.py").exists()
    
    for sub_dir in ["raw", "processed", "models"]:
        sub_path = data_path / sub_dir
        assert sub_path.exists()
        assert (sub_path / "__init__.py").exists()
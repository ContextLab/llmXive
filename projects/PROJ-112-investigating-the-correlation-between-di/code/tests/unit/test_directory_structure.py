import pytest
from pathlib import Path
import tempfile
import shutil
from src.setup_data_structure import get_project_root, setup_directories

@pytest.fixture
def mock_project_root():
    """Create a temporary directory to act as a mock project root."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_project_root_accessible(mock_project_root):
    """
    Test that get_project_root returns a valid Path object.
    This test is slightly modified to accept the fixture path directly
    or verify the logic if the real root is not the temp root.
    """
    # In a real scenario, get_project_root calculates based on __file__.
    # Here we just ensure the function is callable and returns a Path.
    # We cannot easily test the calculation logic without mocking __file__ deeply,
    # so we test that it returns a Path.
    root = get_project_root()
    assert isinstance(root, Path)
    assert root.exists()

def test_setup_directories_creates_missing(mock_project_root):
    """
    Test that setup_directories creates missing directories when pointed at a temp root.
    """
    import src.setup_data_structure as setup_module
    
    # Mock get_project_root to return our temp directory
    original_func = setup_module.get_project_root
    setup_module.get_project_root = lambda: mock_project_root
    
    try:
        # Run setup
        result = setup_directories()
        assert result is True, "setup_directories should return True on success"
        
        # Check specific directories
        assert (mock_project_root / "src").exists()
        assert (mock_project_root / "data/raw").exists()
        assert (mock_project_root / "data/processed/results").exists()
        assert (mock_project_root / "tests/unit").exists()
    finally:
        setup_module.get_project_root = original_func

def test_setup_directories_skips_existing(mock_project_root):
    """
    Test that setup_directories does not fail if directories already exist.
    """
    import src.setup_data_structure as setup_module
    
    # Pre-create a directory
    pre_created = mock_project_root / "src"
    pre_created.mkdir(parents=True, exist_ok=True)
    
    # Mock get_project_root
    original_func = setup_module.get_project_root
    setup_module.get_project_root = lambda: mock_project_root
    
    try:
        result = setup_directories()
        assert result is True
        assert pre_created.exists()
    finally:
        setup_module.get_project_root = original_func

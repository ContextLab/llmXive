import os
import shutil
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# We need to ensure the code directory is in the path for imports
sys_path_backup = __import__('sys').path.copy()
__import__('sys').path.insert(0, 'code')

try:
    from create_results_dirs import main
    from utils import set_task_id, get_logger
finally:
    __import__('sys').path = sys_path_backup


@pytest.fixture
def temp_results_dir():
    """Create a temporary directory to simulate the project root."""
    original_cwd = os.getcwd()
    temp_dir = tempfile.mkdtemp()
    os.chdir(temp_dir)
    yield temp_dir
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)


def test_create_results_dirs_creates_directories(temp_results_dir):
    """Test that main() creates results/ and results/figures/."""
    # Set a mock task ID for the test
    set_task_id("T009")
    
    # Ensure directories don't exist yet
    assert not os.path.exists("results")
    assert not os.path.exists("results/figures")

    # Run the function
    result = main()

    # Assert return code is 0
    assert result == 0

    # Assert directories were created
    assert os.path.exists("results")
    assert os.path.isdir("results")
    assert os.path.exists("results/figures")
    assert os.path.isdir("results/figures")


def test_create_results_dirs_skips_existing(temp_results_dir):
    """Test that main() does not error if directories already exist."""
    set_task_id("T009")

    # Pre-create the directories
    os.makedirs("results")
    os.makedirs("results/figures")

    # Run the function
    result = main()

    # Assert return code is 0
    assert result == 0

    # Assert directories still exist
    assert os.path.exists("results")
    assert os.path.exists("results/figures")

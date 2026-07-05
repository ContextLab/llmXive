import os
import shutil
from pathlib import Path
import pytest
from unittest.mock import patch

# Import the function to test
import code.create_data_raw

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary directory structure mimicking the project root."""
    # Ensure the code directory exists in the temp root
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    
    # Create a dummy setup_directories.py to satisfy imports
    setup_file = code_dir / "setup_directories.py"
    setup_file.write_text(
        "import os\n"
        "from pathlib import Path\n\n"
        "def create_directory(path):\n"
        "    path.mkdir(parents=True, exist_ok=True)\n"
        "    return True\n\n"
        "def main():\n"
        "    pass\n"
    )
    
    return tmp_path

def test_creates_raw_directory(temp_project_root):
    """Test that the script creates the data/raw directory."""
    # Change to the temp project root to simulate running from project root
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_project_root)
        
        # Run the main function
        code.create_data_raw.main()
        
        # Verify the directory was created
        expected_path = temp_project_root / "data" / "raw"
        assert expected_path.exists(), f"Directory {expected_path} was not created."
        assert expected_path.is_dir(), f"{expected_path} exists but is not a directory."
    finally:
        os.chdir(original_cwd)

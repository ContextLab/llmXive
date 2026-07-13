import os
import pytest
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.setup_directories import main

def test_directory_structure_exists(tmp_path, capsys):
    """
    Verify that the setup_directories script creates the required
    directory structure relative to the project root.
    
    We mock the project root by temporarily changing the working directory
    and ensuring the 'code' directory exists as a sibling to 'tests'.
    """
    # Create a temporary project structure
    # tmp_path acts as the project root
    (tmp_path / "code").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tests").mkdir(parents=True, exist_ok=True)
    
    # Change to tmp_path to simulate running the script from project root
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Run the main function
        result = main()
        
        # Verify exit code
        assert result == 0, "main() should return 0 on success"
        
        # Verify directories exist
        assert (tmp_path / "data" / "raw").exists(), "data/raw should exist"
        assert (tmp_path / "data" / "processed").exists(), "data/processed should exist"
        assert (tmp_path / "code").exists(), "code should exist"
        assert (tmp_path / "tests" / "unit").exists(), "tests/unit should exist"
        assert (tmp_path / "tests" / "integration").exists(), "tests/integration should exist"
        
        # Verify output was printed
        captured = capsys.readouterr()
        assert "Setup complete" in captured.out
        
    finally:
        os.chdir(original_cwd)
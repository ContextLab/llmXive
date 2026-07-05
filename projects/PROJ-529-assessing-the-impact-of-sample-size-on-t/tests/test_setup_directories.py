import os
import pytest
import sys

# Add the project root to the path to allow importing code/setup_directories
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.setup_directories import create_directories

def test_create_directories_creates_expected_folders(tmp_path):
    """
    Test that create_directories creates the expected subdirectories
    under the code/ folder relative to the script location.
    """
    # We simulate the environment by temporarily changing the script's 
    # perceived location or by mocking os.path.dirname. 
    # However, since the function relies on __file__, we test the logic
    # by ensuring the function doesn't crash and creates dirs if we 
    # temporarily alter the base logic or verify the side effects.
    
    # For this specific task, we verify that the function runs without error
    # and that the directories it targets (relative to the actual file location)
    # are created or exist.
    
    # Since we cannot easily mock __file__ in a simple test without complex fixtures,
    # we rely on the fact that the script is idempotent.
    # We will run it and check that the directories exist relative to the script.
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # The script is in code/, so we check siblings
    code_dir = os.path.join(script_dir, "code")
    if not os.path.exists(code_dir):
        # If running from tests/ root, code/ should be a sibling
        code_dir = os.path.join(os.path.dirname(script_dir), "code")
    
    # Fallback to the actual file location logic
    import code.setup_directories as sd_module
    script_file_path = sd_module.__file__
    base_dir = os.path.dirname(script_file_path)
    
    expected_dirs = [
        os.path.join(base_dir, "utils"),
        os.path.join(base_dir, "models"),
        os.path.join(base_dir, "tests"),
    ]
    
    # Run the function
    result = create_directories()
    
    # Verify results
    for expected_dir in expected_dirs:
        assert os.path.exists(expected_dir), f"Directory {expected_dir} was not created."
        assert os.path.isdir(expected_dir), f"{expected_dir} is not a directory."

def test_create_directories_is_idempotent():
    """
    Ensure running the function twice does not raise errors.
    """
    # Run twice
    create_directories()
    create_directories()
    # If we reach here without exception, it passed.
    assert True
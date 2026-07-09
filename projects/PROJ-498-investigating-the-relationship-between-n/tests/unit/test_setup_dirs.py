import os
import pytest
from pathlib import Path
import shutil
import tempfile

# We need to import the function from the sibling code directory
# Since tests/unit is at tests/unit, code is at ../code
sys_path_backup = list(__import__('sys').path)
try:
    __import__('sys').path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))
    from setup_dirs import main
finally:
    __import__('sys').path = sys_path_backup

def test_setup_dirs_creates_structure(tmp_path):
    """
    Test that setup_dirs creates the required subdirectories.
    We patch the working directory to a temp folder to avoid polluting the real project.
    """
    # Create a temporary directory structure that mimics the project
    # Project root -> code/ -> setup_dirs.py
    # We will run the script logic against tmp_path
    
    # Mock the project root as tmp_path
    # We need to trick the script into thinking tmp_path is the parent of 'code'
    # But the script uses Path(__file__).parent to find code, then parent for root.
    # To test this purely, we can just verify the logic by calling the internal logic
    # or by setting up a temp structure.
    
    # Let's set up a temp structure:
    # tmp_path
    #   |- code
    #       |- setup_dirs.py (we can't easily move the file, so we test the logic directly)
    
    # Instead, we will test the logic by replicating the directory creation logic
    # in a test-friendly way, or by using a monkeypatch on Path.
    
    # Simpler approach: Just verify that the function calls mkdir correctly on the expected paths.
    # However, the function calculates paths dynamically.
    
    # Let's create a mock environment where tmp_path is the project root.
    # We create a 'code' subfolder in tmp_path and place a copy of the script there?
    # No, let's just test the directory creation logic directly by importing and calling
    # the logic that determines paths, or by mocking the Path resolution.
    
    # Actually, the easiest way to test this specific script is to run it in a temp dir
    # where we have set up the 'code' folder structure.
    
    original_cwd = os.getcwd()
    try:
        # Create structure in tmp_path
        # tmp_path/project_root
        #   |- code/
        # We want tmp_path to be the project root.
        # So we create tmp_path/code/ and run the script from there.
        
        code_folder = tmp_path / "code"
        code_folder.mkdir()
        
        # Copy the script content to the temp code folder
        script_content = (Path(__file__).parent.parent.parent / "code" / "setup_dirs.py").read_text()
        temp_script = code_folder / "setup_dirs.py"
        temp_script.write_text(script_content)
        
        # Change to the temp code folder
        os.chdir(code_folder)
        
        # Run the main function
        exit_code = main()
        
        assert exit_code == 0
        
        # Verify directories exist
        required_dirs = [
            "data/raw",
            "data/processed",
            "data/metrics",
            "data/trial_level",
            "code",
            "tests/unit",
            "tests/integration",
            "contracts",
            "logs"
        ]
        
        for dir_name in required_dirs:
            target = tmp_path / dir_name
            assert target.exists(), f"Directory {dir_name} was not created"
            assert target.is_dir(), f"{dir_name} is not a directory"
            
    finally:
        os.chdir(original_cwd)
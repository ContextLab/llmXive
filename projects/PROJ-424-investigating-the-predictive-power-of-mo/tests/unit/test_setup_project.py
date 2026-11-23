import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add the code directory to the path so we can import setup_project
# This assumes the test is run from the project root
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from setup_project import create_directory_structure

def test_directory_structure_creation():
    """
    Test that create_directory_structure creates the required directories.
    We use a temporary directory to simulate the project root.
    """
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Call the function
            # We need to monkey-patch the root detection logic or pass a root argument
            # Since the current implementation relies on cwd or script location,
            # we will run it in the context of the temp directory.
            # The function detects root as cwd() if script is not named 'setup_project.py' in 'code'
            # To force it to use cwd, we can temporarily rename the script or rely on cwd logic.
            # Let's rely on the cwd logic: if run from tmp_dir, it should use tmp_dir.
            
            # The current implementation:
            # script_path = Path(__file__).resolve() -> points to test file
            # if script_path.name == 'setup_project.py': False
            # code_dir = script_path.parent -> tests/unit
            # if code_dir.name == 'code': False
            # else: root = Path.cwd() -> tmp_dir
            
            create_directory_structure()
            
            # Verify directories
            required_dirs = [
                "code",
                "data/raw",
                "data/processed",
                "data/interim",
                "tests/unit",
                "tests/integration"
            ]
            
            for d in required_dirs:
                target = Path(tmp_dir) / d
                assert target.exists(), f"Directory {target} was not created."
                assert target.is_dir(), f"{target} is not a directory."
                
            print("All required directories were created successfully.")
            
        finally:
            os.chdir(original_cwd)

if __name__ == "__main__":
    test_directory_structure_creation()
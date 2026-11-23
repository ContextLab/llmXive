import os
import tempfile
import pytest
from pathlib import Path
import shutil

# We need to import the function from the module. 
# Since the module is in code/, we adjust the path or import relative to project root.
# Assuming tests are run from project root or with PYTHONPATH set.
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from setup_project_structure import ensure_directories

def test_ensure_directories_creates_structure(tmp_path):
    """
    Test that ensure_directories creates the required folder structure.
    We mock the base path by temporarily changing the working directory 
    or by patching the function to use tmp_path.
    
    Since the function uses Path(__file__).resolve().parent.parent, 
    we will test the logic by creating a temporary directory structure 
    that mimics the project root and verifying the subdirectories are created.
    """
    # Create a temporary project root
    project_root = tmp_path / "mock_project"
    project_root.mkdir()
    
    # Create the code directory to make the path valid for the import logic if needed,
    # but we will test the logic by calling the function in a way that respects tmp_path.
    # Actually, the function is hardcoded to look relative to its file.
    # To test effectively, we will verify the side effects in a temp directory 
    # by temporarily patching the behavior or simply asserting that the logic works.
    
    # Simpler approach: Since we can't easily change the hardcoded path in the imported module
    # without refactoring, we will assert that the function *would* create them if run in a clean env.
    # However, for a robust test, let's create a dummy script in tmp_path that calls the logic.
    
    # Alternative: Just check that the directories exist after running the main entry point
    # in a controlled environment.
    
    # Let's create a test that runs the script in a temp directory.
    original_cwd = os.getcwd()
    original_code_dir = Path(__file__).resolve().parent.parent
    
    try:
        # We cannot easily change the __file__ of the imported module.
        # So we will rely on the fact that if the script runs, it creates the dirs.
        # We will create a temporary directory, copy the script there, run it, and check.
        test_script = project_root / "code" / "test_runner.py"
        test_script.parent.mkdir(parents=True)
        
        # Read the source of the function we want to test
        import inspect
        source = inspect.getsource(ensure_directories)
        
        # Create a standalone test script
        test_script_content = f"""
import os
import sys
from pathlib import Path

# Define the base path as the project root (mock_project)
base_path = Path(r"{project_root}")

def ensure_directories():
    {source.split('def ensure_directories():')[1].split('def ')[0]}

count = ensure_directories()
# Verify
required = ["code", "data/raw", "data/processed", "results/figures", "results/logs", "results/stats", "tests"]
for r in required:
    assert (base_path / r).exists(), f"Missing {{r}}"
print("SUCCESS")
"""
        test_script.write_text(test_script_content)
        
        # Execute the test script
        import subprocess
        result = subprocess.run(
            [sys.executable, str(test_script)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert "SUCCESS" in result.stdout
        
    finally:
        pass

def test_directories_exist_in_project_root():
    """
    Verify that the required directories exist in the actual project root.
    This test assumes the setup script has already been run.
    """
    project_root = Path(__file__).resolve().parent.parent
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "results/figures",
        "results/logs",
        "results/stats",
        "tests"
    ]
    
    for dir_name in required_dirs:
        target = project_root / dir_name
        assert target.exists(), f"Directory {target} does not exist."
        assert target.is_dir(), f"{target} is not a directory."
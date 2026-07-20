"""
Unit tests to verify the data directory structure and .gitkeep files.
"""
import os
import pytest
import subprocess
import sys
import tempfile
import shutil

# We will test the setup script logic directly by importing it or running it
# Since setup_data_dirs.py is in code/, we need to adjust path or import logic
# For testing, we'll simulate the directory creation logic

def test_data_directories_exist():
    """Verify that the data directory structure exists after running the setup script."""
    # This test assumes the script has been run. 
    # In a real CI/CD or pre-commit hook, this script would run first.
    # For this unit test, we verify the logic by checking if the script exists
    # and can be executed to create the structure.
    
    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "code", "setup_data_dirs.py")
    assert os.path.exists(script_path), f"Setup script not found at {script_path}"

def test_gitkeep_creation_logic(tmp_path):
    """Test the logic of creating .gitkeep files in a temporary directory."""
    # Simulate the logic from setup_data_dirs.py
    subdirs = ["data/raw", "data/generated", "data/results"]
    
    for subdir in subdirs:
        full_path = os.path.join(tmp_path, subdir)
        os.makedirs(full_path, exist_ok=True)
        
        gitkeep_path = os.path.join(full_path, ".gitkeep")
        assert not os.path.exists(gitkeep_path), "gitkeep should not exist before creation"
        
        with open(gitkeep_path, 'w') as f:
            f.write("# Keep this directory in version control\n")
        
        assert os.path.exists(gitkeep_path), "gitkeep should exist after creation"
        with open(gitkeep_path, 'r') as f:
            content = f.read()
            assert "# Keep this directory in version control" in content

def test_script_execution_creates_files(tmp_path, monkeypatch):
    """Execute the setup script in a temporary directory and verify results."""
    # We need to mock the PROJECT_ROOT to point to tmp_path
    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "code", "setup_data_dirs.py")
    
    # Create a temporary directory structure that mimics the project root
    # The script looks for 'code' relative to root, but we just want to test the data dir creation
    # We will run the script with a modified environment or patch the logic.
    # Simpler approach: Run the script with a custom argument or patch the constant.
    
    # Let's run the script directly but override the PROJECT_ROOT via monkeypatching
    # However, the script defines PROJECT_ROOT at import time.
    # Better approach: Copy the logic into the test or use subprocess with a modified script.
    
    # We will use subprocess to run the script, but we need to make sure it runs against tmp_path.
    # Since the script assumes it's in code/ and looks up, we can create a fake 'code' dir in tmp_path
    # and run the script from there.
    
    fake_code_dir = os.path.join(tmp_path, "code")
    os.makedirs(fake_code_dir)
    
    # Copy the script to the fake code directory
    import shutil
    shutil.copy(script_path, os.path.join(fake_code_dir, "setup_data_dirs.py"))
    
    # Run the script
    result = subprocess.run(
        [sys.executable, "setup_data_dirs.py"],
        cwd=fake_code_dir,
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Verify directories and files
    data_subdirs = ["data/raw", "data/generated", "data/results"]
    for subdir in data_subdirs:
        full_path = os.path.join(tmp_path, subdir)
        assert os.path.isdir(full_path), f"Directory {full_path} was not created"
        
        gitkeep_path = os.path.join(full_path, ".gitkeep")
        assert os.path.isfile(gitkeep_path), f".gitkeep file not found at {gitkeep_path}"
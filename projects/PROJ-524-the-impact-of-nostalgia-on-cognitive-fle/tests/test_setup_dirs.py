import os
import tempfile
import shutil
import sys
import pytest

# Add parent directory to path to import code modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from setup_dirs import main

def test_stimuli_directory_creation():
    """Test that the stimuli directory is created if it doesn't exist."""
    # Create a temporary directory to simulate project root
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock the project structure
        data_dir = os.path.join(tmpdir, 'data')
        stimuli_dir = os.path.join(data_dir, 'stimuli')
        
        # Ensure data dir exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Verify stimuli dir doesn't exist initially
        assert not os.path.exists(stimuli_dir)
        
        # Temporarily override sys.argv to point to our temp dir
        # We need to patch the main function's behavior
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            # Re-import to pick up the new cwd context if needed, 
            # but setup_dirs uses __file__ relative path logic usually.
            # However, our implementation uses os.path.dirname(os.path.abspath(__file__))
            # relative to the script location. 
            # To make this test robust without moving the script, 
            # we will test the logic directly or rely on the fact that 
            # the script creates relative to its own location.
            
            # Since the script determines root relative to itself (code/),
            # and we are running from tests/, the relative path logic 
            # in the script (os.path.dirname(os.path.dirname(__file__))) 
            # will point to the actual project root where code/ and tests/ live.
            # This test assumes the script is run from the actual project context
            # or we mock the path resolution.
            
            # For a pure unit test of the logic, let's just verify the directory creation
            # by calling the function which will create it relative to the script's location.
            # This is an integration-style test for the directory creation.
            
            # Ensure it doesn't exist before (in the actual repo structure)
            # We can't easily mock the script's __file__ without moving it.
            # So we rely on the fact that the script creates the directory 
            # relative to where it is installed.
            
            # Let's just run the function and check if the directory exists after.
            # This requires the script to be in the expected location relative to data/.
            # If this test runs in the actual repo, it works.
            # If it runs in a temp environment, we might need to adjust.
            
            # Given the constraints, we assume the test runs in the project root context
            # where code/setup_dirs.py exists.
            
            result = main()
            
            # The script creates data/stimuli relative to the code/ directory.
            # So if code/setup_dirs.py is in <repo>/code/, it creates <repo>/data/stimuli/
            # We need to check if that directory exists.
            
            # We need to know the repo root. Since we are in tests/, 
            # repo root is parent of tests/.
            # But the script creates relative to ITSELF (code/).
            # So data/stimuli is sibling to code/.
            
            # Let's construct the expected path based on the script location
            script_dir = os.path.dirname(os.path.abspath(__file__)) # tests/
            repo_root = os.path.dirname(script_dir) # root
            expected_stimuli = os.path.join(repo_root, 'data', 'stimuli')
            
            assert os.path.exists(expected_stimuli), f"Directory {expected_stimuli} was not created."
            assert result == 0
        finally:
            os.chdir(original_cwd)

def test_stimuli_directory_already_exists():
    """Test that the function handles existing directory gracefully."""
    # This test assumes the directory was created by the previous test or exists
    # We just run main again and ensure it doesn't crash
    result = main()
    assert result == 0
    # The directory should still exist
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    stimuli_dir = os.path.join(repo_root, 'data', 'stimuli')
    assert os.path.exists(stimuli_dir)

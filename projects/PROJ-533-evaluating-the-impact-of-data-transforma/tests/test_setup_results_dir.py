import os
import pytest
from pathlib import Path
import shutil

# We need to import the function from the code directory
# Adjusting sys.path to allow import from code/
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_results_dir import main

def test_results_directory_creation(tmp_path):
    """
    Test that the setup_results_dir script creates the results directory.
    We mock the project root by temporarily changing the working directory
    or by patching the Path logic, but since the script uses __file__,
    we test the behavior by ensuring the directory exists after running main
    in a controlled environment.
    
    For this specific task (T001c), we verify that running the script
    ensures the 'results' directory exists relative to the project root.
    """
    # Save original CWD
    original_cwd = os.getcwd()
    
    try:
        # Change to the temporary directory to simulate a fresh project root
        # We need to create a structure that mimics the project:
        # tmp_path (as root)
        #   code/
        #     setup_results_dir.py
        # We will copy the script to tmp_path/code/ and run it
        
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        
        # Copy the script to the temp code dir
        script_source = Path(__file__).parent.parent / "code" / "setup_results_dir.py"
        script_dest = code_dir / "setup_results_dir.py"
        shutil.copy(script_source, script_dest)
        
        # Change to the temp root
        os.chdir(tmp_path)
        
        # Execute the script
        # We need to reload the module to pick up the new path context if we were importing,
        # but here we just run the script logic. Since main() uses __file__ relative to the script,
        # we need to ensure the script is run from the context where __file__ resolves correctly.
        # The script calculates project_root as parent of __file__.
        # If we run the script from tmp_path, __file__ will be tmp_path/code/setup_results_dir.py.
        # project_root will be tmp_path.
        
        # Execute the main function of the copied script
        # We need to exec it or import it. Import is cleaner.
        import importlib.util
        spec = importlib.util.spec_from_file_location("setup_results_dir", script_dest)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Now call main
        module.main()
        
        # Verify the results directory exists
        results_dir = tmp_path / "results"
        assert results_dir.exists(), "The results directory was not created."
        assert results_dir.is_dir(), "The results path exists but is not a directory."
        
    finally:
        # Restore original CWD
        os.chdir(original_cwd)
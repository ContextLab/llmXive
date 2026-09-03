"""
tests/contract/test_data_model_schema.py

Contract test to verify that the data-model.md file matches the required schema.
This test imports and runs the verification logic from code/verify_data_model.py.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add the code directory to the path so we can import the script logic if needed,
# or we can just run the script as a subprocess to ensure it's executable.
# Given the task requirement to "import the verification script", we will do both:
# 1. Ensure the script can be imported (syntax check)
# 2. Run the script to validate the file content.

CODE_DIR = Path(__file__).resolve().parent.parent.parent / "code"
SCRIPT_PATH = CODE_DIR / "verify_data_model.py"

def test_data_model_script_imports():
    """Test that the verification script is syntactically valid and can be imported."""
    try:
        # We need to add the code dir to sys.path to import it as a module
        sys.path.insert(0, str(CODE_DIR))
        import verify_data_model
        assert hasattr(verify_data_model, 'main')
        assert hasattr(verify_data_model, 'validate_schema')
        assert hasattr(verify_data_model, 'extract_entities_from_markdown')
    except ImportError as e:
        raise AssertionError(f"Failed to import verify_data_model: {e}")
    finally:
        # Clean up
        if str(CODE_DIR) in sys.path:
            sys.path.remove(str(CODE_DIR))

def test_data_model_validation():
    """
    Run the verification script to ensure the data-model.md file is valid.
    This executes the script as a subprocess to capture the exit code and output.
    """
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        capture_output=True,
        text=True
    )
    
    # The script should exit with 0 if valid, 1 if invalid
    assert result.returncode == 0, (
        f"Data model validation failed.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )
    
    assert "SUCCESS" in result.stdout, "Expected 'SUCCESS' in output but not found."
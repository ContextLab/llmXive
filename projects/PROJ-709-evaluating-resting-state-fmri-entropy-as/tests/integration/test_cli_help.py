"""
Integration test for Task T040b: Verify Quickstart CLI help.

This test verifies that `python code/main.py --help` displays usage
information without errors, as required by the Quickstart verification.
"""
import subprocess
import sys
import os
import pytest
from pathlib import Path

# Ensure the code directory is in the path for imports if running directly
CODE_DIR = Path(__file__).parent.parent.parent / "code"
os.environ["PYTHONPATH"] = str(CODE_DIR) + ":" + os.environ.get("PYTHONPATH", "")

def test_main_help_command():
    """
    Verify that running `python code/main.py --help` succeeds and outputs help text.
    """
    main_script = Path(__file__).parent.parent.parent / "code" / "main.py"
    
    if not main_script.exists():
        pytest.fail(f"main.py not found at {main_script}")

    try:
        result = subprocess.run(
            [sys.executable, str(main_script), "--help"],
            capture_output=True,
            text=True,
            timeout=30
        )
    except subprocess.TimeoutExpired:
        pytest.fail("Help command timed out")
    except Exception as e:
        pytest.fail(f"Failed to run help command: {e}")

    # Check return code
    if result.returncode != 0:
        pytest.fail(f"Help command failed with return code {result.returncode}.\nStderr: {result.stderr}")

    # Check for expected help content
    output = result.stdout.lower()
    assert "usage" in output or "positional arguments" in output or "optional arguments" in output, \
        "Help output does not contain expected usage information."
    
    # Verify it's not just an error message
    assert "error" not in output or "usage" in output, \
        "Output contains error messages without usage info."

    print("Help output verified successfully:")
    print(result.stdout)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
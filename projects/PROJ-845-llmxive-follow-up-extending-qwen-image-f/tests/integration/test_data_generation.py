"""
Integration test for data generation script.
This test invokes the generator script and expects a SystemExit due to missing implementation.
"""
import subprocess
import sys
import pytest
from pathlib import Path

def test_generator_script_system_exit():
    """
    Test that the generator script exits with SystemExit when implementation is missing.
    This ensures the fail-first approach is working.
    """
    # Path to the generator script
    script_path = Path("code/generators/generate_dataset.py")
    
    if not script_path.exists():
        pytest.skip("Generator script not found, skipping test")
    
    # Run the script and capture the exit code
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True
    )
    
    # Expect a non-zero exit code (SystemExit)
    assert result.returncode != 0, "Expected the script to exit with an error, but it succeeded"
    
    # Verify that the error message indicates missing implementation
    error_output = result.stderr + result.stdout
    assert "NotImplementedError" in error_output or "missing implementation" in error_output.lower(), \
        f"Expected 'missing implementation' error, got: {error_output}"

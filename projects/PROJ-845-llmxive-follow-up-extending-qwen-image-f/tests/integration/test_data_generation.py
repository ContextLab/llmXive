"""
Integration test for User Story 1: Synthetic Dataset Generation.

This test invokes the main generator script to verify the fail-first behavior.
Since the core generation logic (T011-T016) is not yet implemented, the script
is expected to raise a SystemExit with a specific error code indicating
missing implementation.
"""
import subprocess
import sys
import os
import pytest
from pathlib import Path

# Ensure the project root is in the path for imports if running standalone,
# though subprocess handles the environment.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "code"

# Path to the generator script
GENERATOR_SCRIPT = CODE_DIR / "generators" / "generate_dataset.py"

@pytest.mark.integration
def test_generator_fails_on_missing_implementation():
    """
    Verify that running the generator script before implementation
    results in a SystemExit.
    
    According to the task description, the script should fail fast because
    the actual generation logic (T011+) is not present.
    """
    if not GENERATOR_SCRIPT.exists():
        pytest.fail(f"Generator script not found at {GENERATOR_SCRIPT}")

    # Run the script
    result = subprocess.run(
        [sys.executable, str(GENERATOR_SCRIPT)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True
    )

    # Assert that the script exited with a non-zero status
    # We expect SystemExit(1) or similar due to missing implementation
    assert result.returncode != 0, (
        f"Expected generator to fail (SystemExit) due to missing implementation, "
        f"but it exited with code 0.\nStdout: {result.stdout}\nStderr: {result.stderr}"
    )

    # Verify the error message indicates missing implementation
    error_output = result.stderr + result.stdout
    assert "not implemented" in error_output.lower() or "missing" in error_output.lower(), (
        f"Expected error message to mention missing implementation. Got:\n{error_output}"
    )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
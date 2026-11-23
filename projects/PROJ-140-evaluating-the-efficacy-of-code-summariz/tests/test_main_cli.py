import subprocess
import sys
import pytest

def test_main_cli_help_exit_code():
    """
    Verifies that 'python -m code.main --mode sim --help' exits with status 0.
    This satisfies the verification requirement for T001.
    """
    # We use sys.executable to ensure we use the same python environment
    cmd = [sys.executable, "-m", "code.main", "--mode", "sim", "--help"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0, f"CLI failed with exit code {result.returncode}. Stderr: {result.stderr}"
    assert "Code Summarization Bug Localization pipeline" in result.stdout
    assert "--mode" in result.stdout

if __name__ == "__main__":
    # Allow running this test directly via python tests/test_main_cli.py
    pytest.main([__file__])
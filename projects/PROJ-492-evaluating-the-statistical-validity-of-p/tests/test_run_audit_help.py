"""
Test that the audit CLI provides a help message and exits cleanly.
"""
import subprocess
import sys

def test_run_audit_help():
    """Invoke ``python -m code.src.audit.run_audit --help``."""
    result = subprocess.run(
        [sys.executable, "-m", "code.src.audit.run_audit", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"CLI exited with {result.returncode}"
    assert "Run the full A/B test audit pipeline." in result.stdout
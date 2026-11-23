"""
Integration test to verify that the audit CLI provides a help message
and exits with status code 0.
"""
import subprocess
import sys

def test_run_audit_help():
    """Run the audit entry point with --help and assert successful exit."""
    cmd = [sys.executable, "-m", "code.src.audit.run_audit", "--help"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"run_audit --help exited with code {result.returncode}"
    # Optional: ensure help text contains expected sections
    assert "usage:" in result.stdout.lower() or "options:" in result.stdout.lower()

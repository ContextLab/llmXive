"""
Test that the audit CLI provides a help message and exits with status 0.

The verification step for task T001 requires that the following command
runs without error:

    python -m code.src.audit.run_audit --help

This test invokes the module via ``subprocess`` and asserts that the
return code is zero.  No other side‑effects (file creation, network
requests, etc.) are performed.
"""
import subprocess
import sys

def test_run_audit_help_exits_successfully():
    """Execute the module with ``--help`` and verify a zero exit status."""
    result = subprocess.run(
        [sys.executable, "-m", "code.src.audit.run_audit", "--help"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    # The help output should contain the program name; this also ensures
    # that the process completed successfully.
    assert result.returncode == 0, f"Non‑zero exit code: {result.returncode}"
    assert "audit pipeline" in result.stdout.lower() or "usage:" in result.stdout.lower()
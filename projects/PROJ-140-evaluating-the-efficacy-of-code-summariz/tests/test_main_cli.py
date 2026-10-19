"""
Test that the ``code.main`` module can be invoked as a module and that the
``--help`` flag works without error. This mirrors the verification step
described in the quickstart documentation.
"""

import subprocess
import sys

def test_code_main_help():
    """Run ``python -m code.main --mode sim --help`` and assert success."""
    result = subprocess.run(
        [sys.executable, "-m", "code.main", "--mode", "sim", "--help"],
        capture_output=True,
        text=True,
    )
    # The help output should be non‑empty and the process must exit with 0.
    assert result.returncode == 0, f"Non‑zero exit code: {result.returncode}"
    assert "usage:" in result.stdout.lower(), "Help text not found in stdout"
"""
Integration test that verifies the ``run_audit`` module exits with status 0
when invoked with ``--help``.

The test launches the module via ``python -m`` in a subprocess to mimic the
exact command used by the verification step.
"""

import subprocess
import sys
from pathlib import Path


def test_run_audit_help_exits_successfully():
    """
    Execute ``python -m code.src.audit.run_audit --help`` and assert a zero
    exit code. The subprocess is run with the project's root as the working
    directory so that the module can be located via the normal import system.
    """
    # Build the command line exactly as the verification expects
    cmd = [
        sys.executable,
        "-m",
        "code.src.audit.run_audit",
        "--help"
    ]

    # Run the command; capture output to avoid cluttering test logs
    result = subprocess.run(
        cmd,
        cwd=Path(__file__).parents[2],  # project root (two levels up from tests/)
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # The help flag should cause argparse to exit with code 0
    assert result.returncode == 0, (
        f"run_audit --help exited with {result.returncode}\\n"
        f"stdout: {result.stdout}\\nstderr: {result.stderr}"
    )
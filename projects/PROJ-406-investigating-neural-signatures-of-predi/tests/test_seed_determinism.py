"""
Test that the global random seed defined in T000 yields deterministic NumPy output
across separate interpreter invocations.
"""

import subprocess
import sys
import json
import os

def _run_python_command(command: str) -> str:
    """Run a python -c command and return its stdout stripped."""
    result = subprocess.run(
        [sys.executable, "-c", command],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()

def test_numpy_random_determinism():
    # First invocation
    out1 = _run_python_command(
        "import numpy as np; import src; print(np.random.rand())"
    )
    # Second invocation
    out2 = _run_python_command(
        "import numpy as np; import src; print(np.random.rand())"
    )
    assert out1 == out2, f"NumPy random output not deterministic: {out1} != {out2}"

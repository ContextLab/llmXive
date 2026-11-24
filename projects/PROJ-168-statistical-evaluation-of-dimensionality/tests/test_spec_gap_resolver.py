"""
Verify that the spec‑gap resolver script exists and can be executed.
It should simply delegate to the data‑gap resolver.
"""
import subprocess
import sys

def test_spec_gap_resolver_exec():
    result = subprocess.run([sys.executable, "code/spec_gap_resolver.py"], capture_output=True)
    # The script should exit with code 0 regardless of data availability;
    # the pipeline logic decides later.
    assert result.returncode == 0
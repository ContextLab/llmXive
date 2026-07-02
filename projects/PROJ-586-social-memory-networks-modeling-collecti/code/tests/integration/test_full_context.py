import subprocess
import sys
import os
      
def test_full_context_cli():
    script = os.path.abspath("code/run_experiment.py")
    result = subprocess.run(
        [sys.executable, script, "--context", "full", "--agents", "5", "--games", "10"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    # Verify that the expected CSV was created
    expected = os.path.join(
        "projects/PROJ-586-social-memory-networks-modeling-collecti/results",
        "results_full.csv",
    )
    assert os.path.exists(expected)
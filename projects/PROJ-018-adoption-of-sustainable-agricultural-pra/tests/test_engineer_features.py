"""Basic sanity test for the feature‑engineering script."""

import subprocess
import sys
from pathlib import Path


def test_feature_engineering_runs_successfully():
    """Execute ``code/03_engineer_features.py`` and ensure it exits cleanly."""
    script_path = Path("code/03_engineer_features.py")
    # The script should return exit code 0
    result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    # Verify that the expected output file exists
    engineered_path = Path("data/processed/engineered_data.csv")
    assert engineered_path.is_file(), "Engineered data CSV was not created"

# Note: this test is deliberately lightweight – it does not require the
# upstream cleaning step because the repository already contains a small
# synthetic cleaned dataset for CI purposes. If that file is missing the
# test will fail, prompting the developer to generate it first.
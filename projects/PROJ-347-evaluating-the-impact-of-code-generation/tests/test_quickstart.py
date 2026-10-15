import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths

def test_quickstart_runs_successfully(tmp_path: Path):
    """
    Execute the quickstart script and verify that it exits with code 0
    and that the expected artefacts are created.
    """
    # Run the script (it creates its own virtualenv inside the repo)
    result = subprocess.run(
        ["bash", str(paths.code("quickstart.sh"))],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, f"Quickstart failed: {result.stdout}"

    # Expected files
    checksums = paths.data("checksums.json")
    filtered = paths.data("processed", "human_python.csv")
    log_file = paths.logs("quickstart.log")

    for p in (checksums, filtered, log_file):
        assert p.is_file(), f"Expected file {p} was not created"

    # Basic sanity checks on the CSV
    import pandas as pd

    df = pd.read_csv(filtered)
    assert not df.empty, "Filtered CSV should contain rows"
    assert "code" in df.columns, "Column 'code' missing in filtered CSV"
    assert "vulnerability_label" in df.columns, "Label column missing in filtered CSV"
import subprocess
import sys
from pathlib import Path

def test_download_preprocess_runs_successfully():
    """
    End‑to‑end test that the ``download_preprocess`` stage runs without error
    and creates the expected artefacts:
    - data/processed/parcellated/*.csv
    - data/checksums.txt
    - data/processed/exclusion_log.csv
    """
    # Run the stage
    result = subprocess.run(
        [sys.executable, "code/main.py", "--stage", "download_preprocess"],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, f"Pipeline exited with {result.returncode}: {result.stderr}"

    # Verify parcellated CSVs
    parcellated_dir = Path("data/processed/parcellated")
    csv_files = list(parcellated_dir.glob("*_timeseries.csv"))
    assert len(csv_files) >= 1, "No parcellated time‑series CSV files were created."

    # Verify checksums file
    checksums_path = Path("data/checksums.txt")
    assert checksums_path.is_file(), "checksums.txt was not created."

    # Verify exclusion log
    exclusion_log = Path("data/processed/exclusion_log.csv")
    assert exclusion_log.is_file(), "exclusion_log.csv was not created."
    # The log should contain at least one row (subjects missing scores are excluded)
    import pandas as pd
    df = pd.read_csv(exclusion_log)
    assert len(df) >= 1, "Exclusion log is empty; expected at least one exclusion."
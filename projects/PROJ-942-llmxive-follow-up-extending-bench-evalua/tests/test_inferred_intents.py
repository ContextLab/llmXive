"""
Test suite for the deterministic intent inference script (T003).
The test runs the script twice and asserts that the CSV output is identical
and that confidence values lie within the [0, 1] range.
"""

import subprocess
import hashlib
from pathlib import Path

import pandas as pd

# Helper to compute a hash of a file's contents (deterministic check)
def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def test_deterministic_output(tmp_path):
    # Paths relative to the repository root
    input_csv = Path("data/derived/normalized_traces.csv")
    out_csv = tmp_path / "inferred_intents.csv"

    # First run
    subprocess.run(
        [
            "python",
            "code/pipelines/infer_missing_intents.py",
            "--input-csv",
            str(input_csv),
            "--out-csv",
            str(out_csv),
        ],
        check=True,
    )
    hash1 = _file_hash(out_csv)

    # Second run (should produce identical file)
    subprocess.run(
        [
            "python",
            "code/pipelines/infer_missing_intents.py",
            "--input-csv",
            str(input_csv),
            "--out-csv",
            str(out_csv),
        ],
        check=True,
    )
    hash2 = _file_hash(out_csv)

    assert hash1 == hash2, "CSV output is not deterministic across runs"

    # Load CSV and verify confidence column
    df = pd.read_csv(out_csv)
    assert "confidence" in df.columns, "Missing confidence column"
    assert df["confidence"].between(0, 1).all(), "Confidence values out of range"
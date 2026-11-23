"""
Unit tests for the scaffold split script (T004).

The test creates a tiny synthetic dataset with known scaffolds,
runs the split script, and checks that:
  * The three split CSV files exist.
  * No scaffold appears in both train and test.
  * The counts are logged correctly.
"""

import csv
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

# Import the helper that sets seeds – ensures deterministic behaviour
from code.data.download_raw import load_and_set_seeds

SCRIPT = Path("src/preprocessing/scaffold_split.py")

@pytest.fixture
def tiny_dataset(tmp_path: Path):
    """Create a minimal joined.csv with distinct scaffolds."""
    # Simple molecules with distinct Murcko scaffolds
    rows = [
        {"smiles": "CCO", "fqy_raw": 0.1},
        {"smiles": "c1ccccc1", "fqy_raw": 0.2},
        {"smiles": "CCN(CC)CC", "fqy_raw": 0.3},
        {"smiles": "c1ccncc1", "fqy_raw": 0.4},
        {"smiles": "C1CCCCC1", "fqy_raw": 0.5},
        {"smiles": "O=C(O)C", "fqy_raw": 0.6},
    ]
    df = pd.DataFrame(rows)
    input_path = tmp_path / "joined.csv"
    df.to_csv(input_path, index=False)
    return input_path

def run_split(input_path: Path, output_dir: Path):
    """Execute the scaffold split script."""
    cmd = [
        sys.executable,
        "-m",
        "src.preprocessing.scaffold_split",
        "--input",
        str(input_path),
        "--output-dir",
        str(output_dir),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    return result

def test_scaffold_split_creates_files(tmp_path: Path, tiny_dataset: Path):
    out_dir = tmp_path / "splits"
    out_dir.mkdir()
    run_split(tiny_dataset, out_dir)

    # Expected files
    for fname in ["train.csv", "validation.csv", "test.csv", "scaffold_overlap.txt", "split_counts.log"]:
        assert (out_dir / fname).exists(), f"{fname} not created"

    # Load splits
    train = pd.read_csv(out_dir / "train.csv")
    val = pd.read_csv(out_dir / "validation.csv")
    test = pd.read_csv(out_dir / "test.csv")

    # Ensure no scaffold overlap between train and test
    overlap_path = out_dir / "scaffold_overlap.txt"
    overlap_text = overlap_path.read_text().strip()
    assert overlap_text == "train-test overlap: 0", f"Unexpected overlap: {overlap_text}"

    # Verify that each molecule appears in exactly one split
    all_ids = pd.concat([train, val, test])["smiles"].tolist()
    assert sorted(all_ids) == sorted(pd.read_csv(tiny_dataset)["smiles"].tolist())

def test_split_counts_log_warning(tmp_path: Path, tiny_dataset: Path):
    # Create a dataset that will inevitably produce a tiny test set (<20)
    # by using only a few molecules.
    out_dir = tmp_path / "splits2"
    out_dir.mkdir()
    run_split(tiny_dataset, out_dir)

    log_path = out_dir / "split_counts.log"
    lines = log_path.read_text().splitlines()
    # The warning line should be present because the test set will be small
    warning_lines = [l for l in lines if "WARNING:" in l]
    assert warning_lines, "Expected a warning about small test set not found"

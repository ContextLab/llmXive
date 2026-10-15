"""
Unit tests for the SMILES ↔ FQY join script (src.preprocessing.join).

The test creates tiny in‑memory example datasets, writes them to temporary
Parquet/JSON files, runs the join CLI, and checks that:
  * The output CSV is created.
  * The `inchi_key` column exists.
  * The `metadata` column is correctly populated when metadata fields are present.
  * The script aborts with a clear error when the match count is < 200.

These tests use real RDKit functionality but synthetic data of only a few
molecules – this is acceptable for a unit test because it validates the
logic without fabricating the final scientific artefacts.
"""

import json
import pathlib
import subprocess
import sys

import pandas as pd
import pytest

from llmxive_toolkit import paths


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory and ensure llmxive paths resolve inside it."""
    # The llmxive toolkit resolves paths relative to the project root;
    # we monkey‑patch the project root for the duration of the test.
    original_root = paths.root
    paths.root = tmp_path
    yield tmp_path
    paths.root = original_root


def write_smiles_parquet(path: pathlib.Path, smiles_list):
    df = pd.DataFrame({"smiles": smiles_list})
    df.to_parquet(path, index=False)


def write_fqy_json(path: pathlib.Path, records):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f)


def run_join(smiles_path, fqy_path, output_path):
    """Execute the join module via `python -m src.preprocessing.join`."""
    cmd = [
        sys.executable,
        "-m",
        "src.preprocessing.join",
        "--smiles",
        str(smiles_path),
        "--fqy",
        str(fqy_path),
        "--output",
        str(output_path),
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    return result


def test_successful_join(temp_dir):
    """Happy‑path test: 2 matching molecules → join succeeds (match count >= 200 not required
    for the test because we bypass the threshold by providing enough rows)."""
    # Create 250 identical rows to satisfy the >=200 threshold
    smiles = ["C"] * 250  # methane, easy to parse
    fqy_records = [
        {"smiles": "C", "fqy": 0.5, "solvent": "water", "temperature": 298, "measurement_method": "integrating sphere"}
        for _ in range(250)
    ]

    smiles_path = temp_dir / "smiles.parquet"
    fqy_path = temp_dir / "fqy.json"
    output_path = temp_dir / "joined.csv"

    write_smiles_parquet(smiles_path, smiles)
    write_fqy_json(fqy_path, fqy_records)

    result = run_join(smiles_path, fqy_path, output_path)

    # The script should exit with status 0
    assert result.returncode == 0, f"STDERR: {result.stderr}"

    # Verify output file exists and contains expected columns
    out_df = pd.read_csv(output_path)
    assert "inchi_key" in out_df.columns
    assert "metadata" in out_df.columns

    # Metadata should be a JSON string; parse the first entry to check fields
    meta = json.loads(out_df["metadata"].iloc[0])
    assert meta["solvent"] == "water"
    assert meta["temperature"] == 298
    assert meta["measurement_method"] == "integrating sphere"


def test_insufficient_matches_raises(temp_dir):
    """The script must abort when fewer than 200 matches are found."""
    smiles = ["C", "CC"]  # two distinct molecules
    fqy_records = [
        {"smiles": "C", "fqy": 0.5},
        {"smiles": "CC", "fqy": 0.6},
    ]

    smiles_path = temp_dir / "smiles.parquet"
    fqy_path = temp_dir / "fqy.json"
    output_path = temp_dir / "joined.csv"

    write_smiles_parquet(smiles_path, smiles)
    write_fqy_json(fqy_path, fqy_records)

    result = run_join(smiles_path, fqy_path, output_path)

    # Expect non‑zero exit code and an error message mentioning the threshold
    assert result.returncode != 0
    assert "Insufficient matches" in result.stderr or "Insufficient matches" in result.stdout
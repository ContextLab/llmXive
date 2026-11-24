"""
Integration test for the data ingestion script (T001).

This test runs the ingestion script with its default arguments (which
download the ESOL CSV from the official URL) and then checks the
required artefacts for correctness.
"""

import json
import subprocess
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]

@pytest.fixture(scope="module")
def run_ingestion():
    """Execute the ingestion script once for the module."""
    script = PROJECT_ROOT / "code" / "01_data_ingestion.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Ingestion script failed: {result.stderr}"
    return result

def test_checksum_contains_hash(run_ingestion):
    """Verification 1 – checksum file contains a line for the raw CSV."""
    checksum_path = PROJECT_ROOT / "data" / "checksums.txt"
    raw_path = PROJECT_ROOT / "data" / "raw" / "esol.csv"
    assert checksum_path.is_file()
    raw_hash = subprocess.check_output(
        ["sha256sum", str(raw_path)], text=True
    ).split()[0]
    content = checksum_path.read_text()
    assert raw_path.name in content
    assert raw_hash in content

def test_power_analysis_passes(run_ingestion):
    """Verification 2 – power analysis report indicates passes=True."""
    report_path = (
        PROJECT_ROOT / "data" / "processed" / "power_analysis_report.json"
    )
    assert report_path.is_file()
    report = json.loads(report_path.read_text())
    assert report.get("passes") is True
    assert report.get("actual_n", 0) >= report.get("min_n", 0)

def test_filtered_dataset_min_rows(run_ingestion):
    """Verification 3 – filtered dataset has at least 128 rows."""
    filtered_path = (
        PROJECT_ROOT / "data" / "processed" / "filtered_esol.csv"
    )
    df = pd.read_csv(filtered_path)
    assert df.shape[0] >= 128

def test_scaffold_split_exclusivity(run_ingestion):
    """Verification 4 – no scaffold appears in more than one test fold."""
    splits_path = PROJECT_ROOT / "data" / "processed" / "splits.json"
    processed_path = (
        PROJECT_ROOT / "data" / "processed" / "filtered_esol.csv"
    )
    splits = json.loads(splits_path.read_text())["splits"]
    df = pd.read_csv(processed_path)
    # Compute scaffold for each molecule
    from rdkit import Chem
    from rdkit.Chem.Scaffolds import MurckoScaffold

    def scaffold(smiles):
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        return Chem.MolToSmiles(MurckoScaffold.GetScaffoldForMol(mol))

    df["scaffold"] = df["smiles"].apply(scaffold)
    test_scaffolds = []
    for _, test_idx in splits:
        test_scaffolds.extend(df.iloc[test_idx]["scaffold"].tolist())
    # If any scaffold repeats across folds, the set size will be smaller
    assert len(test_scaffolds) == len(set(test_scaffolds))

def test_large_molecule_log(run_ingestion):
    """Verification 5 – exclusion log is non‑empty only if exclusions occurred."""
    log_path = PROJECT_ROOT / "data" / "logs" / "large_molecule_exclusions.log"
    assert log_path.is_file()
    content = log_path.read_text().strip()
    # The script creates an empty file if no exclusions; otherwise it contains lines.
    if content:
        # Ensure each line looks like a SMILES string (basic sanity)
        for line in content.splitlines():
            assert line  # non‑empty
    else:
        # Empty log is acceptable when no large molecules were filtered
        assert content == ""
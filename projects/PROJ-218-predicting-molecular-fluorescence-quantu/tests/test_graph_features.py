"""
Unit test for the ``src.preprocessing.graph_features`` script.

The test creates a tiny CSV file with one valid SMILES (ethanol) and one
deliberately malformed SMILES.  It then invokes the script's ``main`` function
with temporary paths and checks that:

* The Parquet output exists and contains the expected number of rows (1).
* The ``node_features`` and ``edge_features`` columns are present.
* The invalid‑SMILES log contains the malformed entry.
"""

import json
from pathlib import Path

import pandas as pd
import pytest

# Import the CLI entry point from the module we just implemented.
from src.preprocessing.graph_features import main as graph_features_main

@pytest.fixture
def tmp_dataset(tmp_path: Path):
    """Create a minimal CSV with a valid and an invalid SMILES."""
    data = {
        "smiles": ["CCO", "C1CC1XYZ"],  # ethanol (valid) and a broken string
        "fqy_raw": [0.45, 0.30],
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "joined.csv"
    df.to_csv(csv_path, index=False)
    return csv_path

def test_graph_feature_extraction(tmp_path: Path, tmp_dataset: Path):
    output_parquet = tmp_path / "graph_features.parquet"
    log_file = tmp_path / "invalid_smiles.log"

    # Run the script
    exit_code = graph_features_main(
        [
            "--input",
            str(tmp_dataset),
            "--output",
            str(output_parquet),
            "--log",
            str(log_file),
        ]
    )
    assert exit_code == 0, "Script should exit cleanly"

    # Verify Parquet file
    assert output_parquet.is_file(), "Parquet output was not created"
    df_out = pd.read_parquet(output_parquet)
    assert len(df_out) == 1, "Only the valid SMILES should be present"
    assert "node_features" in df_out.columns
    assert "edge_features" in df_out.columns

    # The stored JSON strings should be parseable
    node_feats = json.loads(df_out.iloc[0]["node_features"])
    edge_feats = json.loads(df_out.iloc[0]["edge_features"])
    assert isinstance(node_feats, list) and isinstance(edge_feats, list)

    # Verify the invalid SMILES log
    assert log_file.is_file(), "Invalid SMILES log was not created"
    with open(log_file, "r") as f:
        lines = f.read().strip().splitlines()
    # Expect exactly one line for the malformed SMILES
    assert len(lines) == 1
    smiles_logged, reason = lines[0].split("\t")
    assert smiles_logged == "C1CC1XYZ"
    assert "RDKit failed to parse SMILES" in reason
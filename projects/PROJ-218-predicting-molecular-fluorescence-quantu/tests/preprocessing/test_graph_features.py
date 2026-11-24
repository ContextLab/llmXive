"""
Unit test for ``src.preprocessing.graph_features``.

The test creates a tiny CSV with a mix of valid and invalid SMILES,
runs the ``main`` function, and checks that:
  * The Parquet file is created.
  * Only the valid SMILES are present in the output.
  * The ``invalid_smiles.log`` contains the expected entry.
"""

import pathlib
import pandas as pd
import pyarrow.parquet as pq

from src.preprocessing.graph_features import main


def test_graph_feature_extraction(tmp_path, caplog):
    # ------------------------------------------------------------------
    # Prepare a minimal CSV file
    # ------------------------------------------------------------------
    csv_path = tmp_path / "joined.csv"
    data = {
        "id": [1, 2, 3],
        "smiles": ["CCO", "invalid_smiles", "c1ccccc1"],  # ethanol, bad, benzene
    }
    pd.DataFrame(data).to_csv(csv_path, index=False)

    # ------------------------------------------------------------------
    # Run the extraction script
    # ------------------------------------------------------------------
    output_parquet = tmp_path / "graph_features.parquet"
    exit_code = main(
        [
            "--input",
            str(csv_path),
            "--output",
            str(output_parquet),
        ]
    )
    assert exit_code == 0

    # ------------------------------------------------------------------
    # Verify Parquet content
    # ------------------------------------------------------------------
    assert output_parquet.is_file()
    table = pq.read_table(output_parquet)
    df = table.to_pandas()
    # Only the two valid SMILES should be present
    assert len(df) == 2
    assert set(df["id"]) == {1, 3}
    # Check that feature columns exist and contain list‑like objects
    assert "node_features" in df.columns
    assert "edge_features" in df.columns
    assert isinstance(df.iloc[0]["node_features"], list)
    assert isinstance(df.iloc[0]["edge_features"], list)

    # ------------------------------------------------------------------
    # Verify the invalid SMILES log
    # ------------------------------------------------------------------
    log_path = output_parquet.parent / "invalid_smiles.log"
    assert log_path.is_file()
    log_content = log_path.read_text()
    assert "invalid_smiles" in log_content

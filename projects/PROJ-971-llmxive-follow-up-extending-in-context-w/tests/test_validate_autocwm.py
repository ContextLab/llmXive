import pathlib

import pandas as pd
from llmxive_toolkit import paths

from src.pipeline.validate_autocwm import main

def test_validate_creates_output(tmp_path, monkeypatch):
    """
    End‑to‑end sanity check: the validation script should run without error
    and produce a CSV with the expected columns.
    """
    # Use the real data directories but redirect output to a temporary location
    output_path = tmp_path / "validation_results.csv"
    args = [
        "--descriptors", str(paths.data("descriptors_novel.csv")),
        "--model", str(paths.results("model", "regressor.pt")),
        "--clips-dir", str(paths.data("raw_novel")),
        "--output", str(output_path),
        "--seed", "123",
    ]

    # Run the script
    result_path = main(args)

    # Verify the returned path matches our temporary file
    assert pathlib.Path(result_path) == output_path
    assert output_path.exists()

    # Load and check column names
    df = pd.read_csv(output_path)
    assert set(df.columns) == {"clip_id", "auto_success", "baseline_success"}
    # At least one row should be present (the novel set contains many clips)
    assert len(df) > 0
"""
Integration test for the prompt engineering stage.

The test invokes ``code.prompt_engineering.main`` and verifies that the
expected output files exist and contain the required columns.
"""

import os

from pathlib import Path

import pandas as pd

from llmxive_toolkit import paths

# Import the module under test
from code.prompt_engineering import main as prompt_main


def test_prompt_engineering_creates_outputs(tmp_path: Path, monkeypatch):
    """
    Run the prompt engineering script and check that the parquet and JSON
    artifacts are produced with the correct schema.
    """
    # Ensure the project‑wide data directories point inside the temporary
    # directory provided by pytest.  The ``paths`` helper creates directories
    # relative to the repository root, so we monkey‑patch its ``root`` attribute
    # to point at the temporary location.
    monkeypatch.setattr("llmxive_toolkit.paths.root", tmp_path, raising=False)

    # Run the main function – this should create the fallback commit messages
    # parquet (if not already present) and then the intent prompts files.
    prompt_main()

    # Define expected output locations
    parquet_path = paths.data("processed", "intent_prompts.parquet")
    json_path = paths.data("processed", "intent_prompts.json")

    # Verify files exist
    assert parquet_path.is_file(), f"Parquet file not found at {parquet_path}"
    assert json_path.is_file(), f"JSON file not found at {json_path}"

    # Load parquet and check required columns
    df = pd.read_parquet(parquet_path)
    expected_cols = {"pr_id", "prompt", "complexity_indicator"}
    assert expected_cols.issubset(set(df.columns)), f"Missing columns in parquet: {expected_cols - set(df.columns)}"
    assert len(df) > 0, "Parquet file should contain at least one row"

    # Load JSON and perform a lightweight sanity check
    df_json = pd.read_json(json_path)
    assert set(df_json.columns) == expected_cols, "JSON columns do not match expected schema"
    assert df_json["complexity_indicator"].isin(["simple", "moderate", "complex"]).all(), "Invalid complexity indicator in JSON"
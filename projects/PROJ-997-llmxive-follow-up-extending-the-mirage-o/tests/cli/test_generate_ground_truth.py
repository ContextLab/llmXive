"""
Integration test for the ground‑truth generation pipeline (T015).

The test runs the wrapper script with a tiny sample size using the
lightweight ``distilgpt2`` model and a single quantisation level.
It checks that:
  * The Parquet dataset file is created.
  * The file contains the expected columns.
  * The JSON statistics file is written and has the correct top‑level key.
"""
import json
from pathlib import Path

import pandas as pd
import pytest

# Import the wrapper function from the data‑generation script.
from code.data.generate_ground_truth import run_wrapper

@pytest.mark.timeout(300)
def test_generate_ground_truth(tmp_path):
    # Define output locations inside the repository's data folder.
    parquet_path = Path("data/processed/test_sample.parquet")
    stats_path = Path("data/processed/dataset_stats.json")

    # Clean any previous artefacts that might interfere with the test.
    if parquet_path.is_file():
        parquet_path.unlink()
    if stats_path.is_file():
        stats_path.unlink()

    # Run the pipeline with a very small sample to keep the test fast.
    run_wrapper(
        model="distilgpt2",
        levels=["INT8"],          # single level is sufficient for the test
        output_path=str(parquet_path),
        sample_size=5,            # tiny dataset – runs quickly on CI
    )

    # -----------------------------------------------------------------
    # Verify that the Parquet file exists and has the required schema.
    # -----------------------------------------------------------------
    assert parquet_path.is_file(), "Parquet output was not created"
    df = pd.read_parquet(parquet_path)
    assert not df.empty, "Parquet file is empty"
    required_columns = {
        "input_id",
        "quantization_level",
        "gradient_norm",
        "local_curvature",
        "kl_divergence",
    }
    assert required_columns.subset(df.columns), "Missing expected columns in dataset"

    # -----------------------------------------------------------------
    # Verify that the statistics JSON file exists and contains the expected
    # top‑level keys produced by the wrapper.
    # -----------------------------------------------------------------
    assert stats_path.is_file(), "Statistics JSON was not created"
    with open(stats_path, "r", encoding="utf-8") as f:
        stats = json.load(f)

    assert "per_level_statistics" in stats, "Statistics JSON missing required key"
    assert "overall_non_zero_kl_significant" in stats, "Statistics JSON missing overall flag"

    # Clean up after the test to avoid contaminating later runs.
    parquet_path.unlink()
    stats_path.unlink()
"""
Test the counterfactual generation pipeline on a tiny subset of videos.

The test streams the Something‑Something V2 dataset, asks the
``counterfactual`` module to process two videos, and verifies that at
least one accepted pair has an optical‑flow divergence ≤ 0.15.
"""

import pathlib
import sys

import pytest

# Ensure the project root is on the import path
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from src.data.counterfactual import CounterfactualGenerator, main as cf_main
from src.data.something_loader import something_stream

@pytest.mark.timeout(300)
def test_counterfactual_generation(tmp_path):
    """
    Run the counterfactual generator on a 2‑video mini‑subset and assert
    that at least one pair satisfies the divergence constraint.
    """
    # Parameters – keep everything inside the temporary directory
    output_dir = tmp_path / "output"
    patch_dir = pathlib.Path("data/patches")
    # Use a deterministic seed for reproducibility
    seed = 123

    # Run the CLI entry point (it writes the metadata CSV)
    args = [
        "--subset_size",
        "2",
        "--output_dir",
        str(output_dir),
        "--optical_flow_divergence_threshold",
        "0.15",
        "--feature_similarity_threshold",
        "0.9",
        "--patch_dir",
        str(patch_dir),
        "--seed",
        str(seed),
    ]
    # Directly invoke the main function to avoid subprocess overhead
    ret = cf_main(args)
    assert ret == 0, "counterfactual script exited with non‑zero status"

    metadata_path = output_dir / "data" / "counterfactuals" / "metadata.csv"
    assert metadata_path.is_file(), "metadata.csv not created"

    import pandas as pd

    df = pd.read_csv(metadata_path)
    # If no rows were accepted, the test should fail – we expect at least one
    assert not df.empty, "No counterfactual pairs were accepted"

    # Verify the divergence constraint for at least one row
    assert (
        (df["optical_flow_divergence"] <= 0.15).any()
    ), "No accepted pair meets the optical‑flow divergence threshold"

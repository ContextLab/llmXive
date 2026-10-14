"""
Unit test for src/data/latent_generator.py

The test runs the latent generator on a tiny synthetic dataset
consisting of a single image from the real PubLayNet download.
It verifies that:
  * The output parquet contains a ``visual_latent`` column.
  * Each latent has length 768 and contains no NaNs.
  * The runtime log file is created.
"""
import os
import shutil
from pathlib import Path

import pandas as pd
import pytest

from src.data.latent_generator import main as generate_latents
from llmxive_toolkit import paths

@pytest.fixture(scope="module")
def tiny_dataset(tmp_path_factory):
    """
    Create a minimal dataset with one real image from the downloaded PubLayNet
    (the download script is executed beforehand in the CI pipeline).
    """
    # Locate the PubLayNet raw directory (the download script stores it under data/raw/publaynet)
    raw_dir = Path("data/raw/publaynet")
    if not raw_dir.is_dir():
        pytest.skip("PubLayNet dataset not downloaded; cannot run latent generation test.")
    # Find the first image file
    image_path = next(raw_dir.rglob("*.png"))
    # Build a minimal parquet with the required columns
    df = pd.DataFrame(
        [
            {
                "doc_id": "test-doc-1",
                "plain_text": "placeholder OCR text",
                "layout_annotations": [],
                "image_path": str(image_path),
                "source": "real",
            }
        ]
    )
    input_parquet = tmp_path_factory.mktemp("input") / "document_pairs.parquet"
    df.to_parquet(input_parquet, index=False)
    return input_parquet

def test_latent_generation(tmp_path, tiny_dataset):
    output_parquet = tmp_path / "document_pairs_with_latent.parquet"

    # Run the generator (using the same CLI signature as the script)
    generate_latents(
        [
            "--input-parquet",
            str(tiny_dataset),
            "--output-parquet",
            str(output_parquet),
            "--encoder-name",
            "layoutlmv3-base",
            "--device",
            "cpu",
        ]
    )

    # Verify output parquet exists and has the expected column
    assert output_parquet.is_file()
    out_df = pd.read_parquet(output_parquet)
    assert "visual_latent" in out_df.columns
    assert len(out_df) == 1

    latent = out_df["visual_latent"].iloc[0]
    assert isinstance(latent, list)
    assert len(latent) == 768
    # No NaNs
    assert all(v == v for v in latent)

    # Verify runtime log was written
    runtime_path = paths.results("runtime", "latent_inference_seconds.txt")
    assert runtime_path.is_file()
    with open(runtime_path) as f:
        content = f.read().strip()
        assert float(content) > 0.0
"""
Unit test for the preprocessing script.

It creates a tiny synthetic PubLayNet‑style directory structure with one
image and a matching JSON annotation, runs the preprocess script, and checks
that the resulting Parquet file exists and contains the expected columns.
"""

import os
import shutil
from pathlib import Path

import pandas as pd
import pytest

from src.data.preprocess import preprocess_dataset

@pytest.fixture
def tiny_dataset(tmp_path: Path):
    # Create a minimal image (white 100x100 PNG)
    img_path = tmp_path / "sample.png"
    img_path.parent.mkdir(parents=True, exist_ok=True)
    from PIL import Image

    Image.new("RGB", (100, 100), color="white").save(img_path)

    # Create a matching annotation JSON
    ann_path = tmp_path / "sample.json"
    ann_content = {
        "objects": [
            {
                "category": "text_block",
                "bbox": {"x0": 10, "y0": 10, "x1": 90, "y1": 20},
            }
        ]
    }
    with ann_path.open("w", encoding="utf-8") as f:
        import json

        json.dump(ann_content, f)

    return tmp_path

def test_preprocess_creates_parquet(tiny_dataset: Path, tmp_path: Path):
    output_parquet = tmp_path / "out.parquet"
    # Use the path defined in the spec/quickstart
    schema_path = Path("contracts/documentpair.schema.yaml")

    # Run the preprocessing
    preprocess_dataset(tiny_dataset, output_parquet, schema_path)

    # Verify Parquet output
    assert output_parquet.is_file()
    df = pd.read_parquet(output_parquet, engine="pyarrow")
    expected_cols = {"doc_id", "plain_text", "layout_annotations", "image_path", "source"}
    assert expected_cols.issubset(set(df.columns))
    # Basic sanity checks
    assert len(df) == 1
    assert df.iloc[0]["doc_id"] == "sample"
"""
Unit test for the OCR fallback extractor.

The test creates a minimal CSV with a single row that references a
generated blank PNG image. The OCR libraries are optional; if they are
unavailable the extractor should simply leave the PSD columns as NaN and
must **not** drop the row.
"""
import pandas as pd
import numpy as np
import tempfile
from pathlib import Path

from src.ingest.ocr_extractor import process_ocr

def test_ocr_extractor_preserves_rows(tmp_path: Path):
    # Create a dummy white image (will not contain any numbers)
    from PIL import Image

    img_path = tmp_path / "blank.png"
    Image.new("RGB", (100, 100), color="white").save(img_path)

    # Build a tiny DataFrame with missing PSD values
    df = pd.DataFrame(
        {
            "experiment_id": ["test_001"],
            "psd_image_path": [str(img_path)],
            "d10": [np.nan],
            "d50": [np.nan],
            "d90": [np.nan],
        }
    )

    # Run the OCR processing – should not raise and should keep one row
    result = process_ocr(df)

    assert len(result) == 1, "Row count changed after OCR processing"
    # Since the image is blank, OCR will not find numbers; columns stay NaN
    assert pd.isna(result.loc[0, "d10"])
    assert pd.isna(result.loc[0, "d50"])
    assert pd.isna(result.loc[0, "d90"])
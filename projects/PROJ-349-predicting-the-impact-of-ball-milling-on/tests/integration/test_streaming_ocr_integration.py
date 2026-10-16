"""
Integration test for ``src.ingest.streaming_ocr_integration``.

The test creates a temporary CSV file containing a single row with a
``psd_image_path`` that points to a tiny text file.  The OCR extractor
helpers are designed to work with plain‑text files as a fallback – they
simply read the file contents.  The text file contains the three PSD
metrics (d10, d50, d90) in a format that ``_extract_numbers_from_text``
can recognise.

The test verifies that:
  * The streaming function returns a DataFrame with the expected columns.
  * The extracted numeric values are correctly populated.
  * No exception propagates out of the integration layer.
"""

import csv
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.ingest.streaming_ocr_integration import stream_with_ocr

@pytest.fixture
def dummy_psd_file(tmp_path: Path) -> Path:
    """
    Create a tiny text file that mimics OCR output.
    """
    content = "d10: 12.3\\n d50: 45.6 \\n d90: 78.9"
    file_path = tmp_path / "psd_dummy.txt"
    file_path.write_text(content, encoding="utf-8")
    return file_path

@pytest.fixture
def input_csv(tmp_path: Path, dummy_psd_file: Path) -> Path:
    """
    Write a CSV with a single row that references the dummy PSD file.
    """
    csv_path = tmp_path / "input.csv"
    # Minimal required columns for the streaming pipeline.
    rows = [
        {
            "experiment_id": "exp_001",
            "psd_image_path": str(dummy_psd_file),
            # other columns are optional for this test
        }
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return csv_path

def test_streaming_ocr_integration_basic(input_csv: Path):
    """
    Verify that the OCR fallback populates ``d10``, ``d50`` and ``d90``.
    """
    # Stream the CSV in a single chunk (the file is tiny).
    df_iterator = pd.read_csv(input_csv, chunksize=10)

    result_df = stream_with_ocr(df_iterator)

    # The result should contain the original row plus the three PSD columns.
    assert "d10" in result_df.columns
    assert "d50" in result_df.columns
    assert "d90" in result_df.columns

    # Validate the extracted numeric values.
    row = result_df.iloc[0]
    assert pytest.approx(row["d10"], rel=1e-6) == 12.3
    assert pytest.approx(row["d50"], rel=1e-6) == 45.6
    assert pytest.approx(row["d90"], rel=1e-6) == 78.9
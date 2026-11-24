"""Unit tests for the download step (T001)."""

from __future__ import annotations

import pandas as pd
import pytest
import json
from llmxive_toolkit import paths
from code.src.data.download import collect_prompt_sample

RAW_PARQUET = paths.data("raw", "prompts_sample.parquet")
MANIFEST_PATH = paths.data("raw", "checksums_manifest.json")

def test_downloaded_sample_meets_task_check():
    """Verify the produced artifacts meet the T001 specifications."""
    assert RAW_PARQUET.exists(), "Parquet file was not created"
    assert MANIFEST_PATH.exists(), "Manifest file was not created"

    df = pd.read_parquet(RAW_PARQUET)
    assert len(df) >= 2000, f"Expected at least 2000 rows, found {len(df)}"
    assert "prompt" in df.columns, "Column 'prompt' missing from parquet"
    assert df["prompt"].notna().all(), "Found null values in 'prompt' column"
    assert df["checksum"].notna().all(), "Found null values in 'checksum' column"

    with open(MANIFEST_PATH, 'r') as f:
        manifest = json.load(f)
    
    assert len(manifest) >= 2000, "Manifest contains too few entries"
    # Check a few random samples for consistency
    for i in range(0, 2000, 500):
        row = df.iloc[i]
        assert manifest[str(row['row_id'])] == row['checksum'], f"Checksum mismatch at row {i}"

def test_collect_prompt_sample_fails_loudly_on_short_stream(monkeypatch):
    """Verify that the loader raises RuntimeError if the stream is too short."""
    # Mock _iter_stream_hf to return only 10 rows
    def mock_stream():
        for i in range(10):
            yield {"prompt": f"prompt {i}", "original_prompt": "orig"}
    
    monkeypatch.setattr("code.src.data.download._iter_stream_hf", mock_stream)
    
    with pytest.raises(RuntimeError, match="Collected only 10 valid prompts"):
        collect_prompt_sample(n_prompts=2000)
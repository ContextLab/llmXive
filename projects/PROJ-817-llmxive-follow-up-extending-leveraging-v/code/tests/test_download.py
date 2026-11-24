"""Unit tests for the T001 real-data downloader."""

from __future__ import annotations

import pandas as pd
import pytest

from code.src.data.download import (
    N_PROMPTS,
    OUTPUT_PATH,
    _row_checksum,
    collect_prompt_sample,
)


def test_row_checksum_is_deterministic_and_sensitive():
    row = {"edit_prompt": "make it snow", "original_prompt": "a beach",
           "edit_type": "weather"}
    c1 = _row_checksum(row)
    assert c1 == _row_checksum(dict(row))
    assert len(c1) == 64
    row2 = dict(row, edit_prompt="make it rain")
    assert _row_checksum(row2) != c1


@pytest.mark.skipif(
    not OUTPUT_PATH.exists(), reason="prompts_sample.parquet not yet downloaded"
)
def test_downloaded_sample_meets_task_check():
    df = pd.read_parquet(OUTPUT_PATH)
    assert len(df) >= N_PROMPTS
    assert df["edit_prompt"].notna().all()
    assert (df["edit_prompt"].str.strip() != "").all()
    assert df["checksum"].notna().all()
    assert not df["checksum"].duplicated().any()
    assert df["checksum"].str.fullmatch(r"[0-9a-f]{64}").all()


def test_collect_prompt_sample_fails_loudly_on_short_stream(monkeypatch):
    """No synthetic fallback: a stream with too few rows must raise."""
    import code.src.data.download as dl

    def fake_stream():
        yield {"edit_prompt": "only one real row",
               "original_prompt": "x", "edit_type": "t"}

    monkeypatch.setattr(dl, "_iter_stream_hf", fake_stream)
    with pytest.raises(RuntimeError):
        dl.collect_prompt_sample(n_prompts=5)
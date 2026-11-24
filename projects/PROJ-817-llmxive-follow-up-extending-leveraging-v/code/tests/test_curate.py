"""Unit tests for the curation step (T002)."""

from __future__ import annotations

import pandas as pd
import pytest

from llmxive_toolkit import paths

CSV_PATH = paths.results("curated_prompts.csv")


@pytest.mark.skipif(not CSV_PATH.exists(), reason="Curated CSV not yet generated")
def test_curated_csv_has_balanced_classes():
    df = pd.read_csv(CSV_PATH)
    assert len(df) == 1000, "CSV must contain exactly 1 000 rows"
    counts = df["instruction_type"].value_counts()
    assert counts.get("neutral", 0) == 500, "Should have 500 neutral prompts"
    assert counts.get("conflict", 0) == 500, "Should have 500 conflicting prompts"


@pytest.mark.skipif(not CSV_PATH.exists(), reason="Curated CSV not yet generated")
def test_checksum_and_human_score_columns():
    df = pd.read_csv(CSV_PATH)
    # checksum must be non‑null and look like a SHA‑256 hex string
    assert df["checksum"].notna().all()
    assert df["checksum"].str.fullmatch(r"[0-9a-f]{64}").all()
    # human_score must be null for all rows at this stage
    assert df["human_score"].isna().all()

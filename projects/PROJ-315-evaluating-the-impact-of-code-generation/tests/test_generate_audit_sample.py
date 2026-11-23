"""Tests for the audit sample generation script (T017a)."""

import pathlib
import pandas as pd

from code.data.generate_audit_sample import (
    load_classified_data,
    select_audit_sample,
    write_audit_csv,
)


def test_load_classified_data(tmp_path: pathlib.Path):
    # Create a minimal parquet file for the test
    df = pd.DataFrame(
        {
            "pr_id": ["PR-1"],
            "commit_message": ["Fix bug"],
            "code_snippet": ["def foo(): pass"],
            "is_llm_generated": [False],
        }
    )
    parquet_path = tmp_path / "classified.parquet"
    df.to_parquet(parquet_path)

    loaded = load_classified_data(parquet_path)
    assert isinstance(loaded, pd.DataFrame)
    assert loaded.equals(df)


def test_select_audit_sample():
    df = pd.DataFrame(
        {
            "pr_id": [f"PR-{i}" for i in range(1, 6)],
            "commit_message": [f"msg{i}" for i in range(1, 6)],
            "code_snippet": [f"code{i}" for i in range(1, 6)],
        }
    )
    sample = select_audit_sample(df, sample_size=3, seed=42)
    # Should contain exactly the three requested columns
    assert list(sample.columns) == ["pr_id", "commit_message", "code_snippet"]
    assert len(sample) == 3
    # Deterministic ordering by pr_id after sampling
    assert list(sample["pr_id"]) == sorted(sample["pr_id"])


def test_write_audit_csv(tmp_path: pathlib.Path):
    df = pd.DataFrame(
        {
            "pr_id": ["PR-1", "PR-2"],
            "commit_message": ["msg1", "msg2"],
            "code_snippet": ["code1", "code2"],
        }
    )
    out_path = tmp_path / "audit_unlabeled.csv"
    write_audit_csv(df, out_path)

    # Verify file exists and can be read back correctly
    read_back = pd.read_csv(out_path)
    assert read_back.equals(df)
"""Unit tests for the T007 sampling artifact."""

import json
from pathlib import Path

from llmxive_toolkit import paths


def test_sample_functions_jsonl_has_800_rows():
    output = paths.data("raw", "sample_functions.jsonl")
    assert output.exists(), (
        f"{output} does not exist; run code/sample_functions.py first"
    )
    rows = [
        json.loads(line)
        for line in output.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(rows) == 800
    for row in rows:
        assert isinstance(row["code"], str) and row["code"].strip()
        assert "repo" in row and "language" in row
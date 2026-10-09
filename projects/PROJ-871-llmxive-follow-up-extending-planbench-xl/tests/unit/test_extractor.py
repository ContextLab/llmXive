"""
Unit test for the ``extractor.py`` module.

The test creates a minimal synthetic parquet file containing a handful of
records, invokes the extractor, and then checks that the output JSONL file
contains only the rows whose ``ground_truth`` field equals
``\"implicit_failure\"``.
"""

import json
import os
import shutil
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

# Import the function directly – no need to run the CLI.
from dataset.extractor import extract_implicit_failure_subset, _stream_raw_dataset

@pytest.fixture
def synthetic_raw_dir(tmp_path: Path) -> Path:
    """
    Create a temporary ``data/raw`` directory containing a single parquet file
    with a small number of records.  Two records have
    ``ground_truth == "implicit_failure"``, the others do not.
    """
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True)

    records = [
        {"task_id": "t1", "prompt": "Q1", "ground_truth": "success"},
        {"task_id": "t2", "prompt": "Q2", "ground_truth": "implicit_failure"},
        {"task_id": "t3", "prompt": "Q3", "ground_truth": "implicit_failure"},
        {"task_id": "t4", "prompt": "Q4", "ground_truth": "success"},
    ]

    # Convert to Arrow table and write a parquet file.
    table = pa.Table.from_pylist(records)
    parquet_path = raw_dir / "sample.parquet"
    pq.write_table(table, parquet_path)

    return raw_dir

def test_stream_raw_dataset_yields_all_rows(synthetic_raw_dir: Path):
    """The streaming helper should yield exactly the number of rows written."""
    rows = list(_stream_raw_dataset(synthetic_raw_dir))
    assert len(rows) == 4
    # Verify a couple of fields to ensure data integrity.
    assert rows[0]["task_id"] == "t1"
    assert rows[2]["ground_truth"] == "implicit_failure"

def test_extract_implicit_failure_subset(synthetic_raw_dir: Path, tmp_path: Path):
    """Only rows with ground_truth == 'implicit_failure' should be written."""
    output_path = tmp_path / "implicit_failure_subset.jsonl"

    # Run the extractor.
    result_path = extract_implicit_failure_subset(synthetic_raw_dir, output_path)

    # The function should return the exact path we passed.
    assert result_path == output_path

    # Read the JSONL output.
    with open(output_path, "r", encoding="utf-8") as f:
        lines = [json.loads(line) for line in f if line.strip()]

    # Expect exactly the two rows with the target ground truth.
    assert len(lines) == 2
    for entry in lines:
        assert entry["ground_truth"] == "implicit_failure"
        assert entry["task_id"] in {"t2", "t3"}
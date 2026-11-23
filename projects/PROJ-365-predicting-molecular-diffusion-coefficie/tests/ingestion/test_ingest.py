"""
Unit test for the end‑to‑end ingestion orchestrator (code/ingestion/ingest.py).

The test verifies that:
1. ``ingest`` returns ``True``.
2. The output JSONL file exists.
3. The number of JSON lines equals the count recorded in
   ``data/processed/valid_record_count.txt``.
"""

import json
from pathlib import Path

from utils.config import get_project_root
from ingestion.ingest import ingest

def test_ingest_end_to_end(tmp_path):
    """
    Run the ingestion pipeline on the project's current dataset and
    assert consistency between the JSONL output and the recorded valid
    record count.
    """
    # Use the real project root; the test runs in the repository context.
    root = get_project_root()

    # Ensure a clean state: remove any previous processed artifacts.
    processed_dir = root / "data" / "processed"
    jsonl_path = processed_dir / "featurized_data.jsonl"
    count_path = processed_dir / "valid_record_count.txt"

    if jsonl_path.is_file():
        jsonl_path.unlink()
    if count_path.is_file():
        count_path.unlink()

    # Execute the ingestion pipeline.
    assert ingest(root) is True

    # Verify the JSONL output exists.
    assert jsonl_path.is_file(), f"Expected JSONL output at {jsonl_path}"

    # Count JSON lines.
    with jsonl_path.open("r", encoding="utf-8") as f:
        jsonl_lines = [line for line in f if line.strip()]

    # Verify the count file exists and matches.
    assert count_path.is_file(), f"Expected count file at {count_path}"
    recorded_count = int(count_path.read_text().strip())
    assert recorded_count == len(jsonl_lines), (
        f"Recorded count ({recorded_count}) does not match number of JSONL lines "
        f"({len(jsonl_lines)})"
    )
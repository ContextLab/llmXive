"""
Unit test to ensure that the ingestion orchestrator writes a
``valid_record_count.txt`` that matches the number of JSON‑L records
produced.
"""

import json
from pathlib import Path

def test_valid_count_matches_jsonl():
    root = Path.cwd()
    count_path = root / "data" / "processed" / "valid_record_count.txt"
    jsonl_path = root / "data" / "processed" / "featurized_data.jsonl"

    # Ensure both files exist
    assert count_path.is_file(), "valid_record_count.txt missing"
    assert jsonl_path.is_file(), "featurized_data.jsonl missing"

    # Read count
    count = int(count_path.read_text(encoding="utf-8").strip())

    # Count JSON‑L lines
    with jsonl_path.open("r", encoding="utf-8") as f:
        jsonl_lines = [line for line in f if line.strip()]

    assert count == len(jsonl_lines), (
        f"Count mismatch: {count} recorded vs {len(jsonl_lines)} JSON‑L lines"
    )
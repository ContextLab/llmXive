import json
from pathlib import Path
import pytest
from llmxive_toolkit import paths

def test_download_artifacts_exist():
    """Verify that the download script produced the required files."""
    raw_path = paths.data("raw_snippets.jsonl")
    excluded_path = paths.data("excluded_records.json")
    hashes_path = paths.data("artifact_hashes.yaml")
    
    assert raw_path.is_file(), "raw_snippets.jsonl missing"
    assert excluded_path.is_file(), "excluded_records.json missing"
    assert hashes_path.is_file(), "artifact_hashes.yaml missing"

def test_raw_snippets_validity():
    """Verify that raw_snippets.jsonl contains valid records and meets minimum count."""
    raw_path = paths.data("raw_snippets.jsonl")
    records = []
    with raw_path.open("r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    
    assert len(records) >= 50, f"Expected at least 50 valid snippets, found {len(records)}"
    for r in records:
        assert "snippet_id" in r
        assert "code" in r and r["code"].strip()
        assert "human_comment" in r and r["human_comment"].strip()

def test_excluded_records_structure():
    """Verify that excluded_records.json is a list of records with reasons."""
    excluded_path = paths.data("excluded_records.json")
    with excluded_path.open("r", encoding="utf-8") as f:
        excluded = json.load(f)
    
    assert isinstance(excluded, list)
    for r in excluded:
        assert "reason" in r, "Excluded record missing 'reason' field"
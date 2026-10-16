"""Unit tests for data_fetcher.py.

Verifies that real datasets are fetched and contain data.
"""
import pytest
import os
from pathlib import Path
from code.utils.data_fetcher import fetch_dataset, DataFetchError

def test_fetch_ms_marco(tmp_path):
    """Test fetching MS MARCO results in a non-empty file."""
    dest = tmp_path / "ms_marco_test.jsonl"
    path = fetch_dataset("ms_marco", dest_path=dest)
    assert path.is_file()
    assert path.stat().st_size > 0
    with path.open("r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) > 0

def test_fetch_spider(tmp_path):
    """Test fetching Spider results in a non-empty file."""
    dest = tmp_path / "spider_test.jsonl"
    path = fetch_dataset("spider", dest_path=dest)
    assert path.is_file()
    assert path.stat().st_size > 0
    with path.open("r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) > 0

def test_fetch_dbpedia(tmp_path):
    """Test fetching DBpedia TTL results in a non-empty file."""
    dest = tmp_path / "dbpedia_test.ttl"
    path = fetch_dataset("dbpedia_sample", dest_path=dest)
    assert path.is_file()
    assert path.stat().st_size > 0
    with path.open("rb") as f:
        content = f.read()
        assert len(content) > 0
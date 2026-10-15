"""Unit tests for the data_fetcher module.

The tests verify that a real row is fetched from each required source.
They rely on the real HuggingFace datasets and the public TTL file.
"""

import json
import os

from pathlib import Path

import pytest

from utils.data_fetcher import fetch_dataset, verify_all_datasets, DataFetchError

# Helper to read the first JSON line from a file
def _first_line_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                return json.loads(line)
    raise ValueError(f"No JSON lines found in {path}")

@pytest.fixture(scope="module")
def raw_dir(tmp_path_factory):
    """Create a temporary raw data directory and point the toolkit paths there."""
    raw = tmp_path_factory.mktemp("raw")
    # Monkey‑patch the llmxive_toolkit paths to use the temp directory.
    from llmxive_toolkit import paths as toolkit_paths

    original_raw = toolkit_paths.data
    toolkit_paths.data = lambda *parts: Path(raw, *parts)
    yield raw
    # Restore original function after the tests
    toolkit_paths.data = original_raw

def test_fetch_ms_marco_first_row(raw_dir):
    dest = raw_dir / "ms_marco_train.jsonl"
    path = fetch_dataset(
        name="ms_marco",
        config_name="v1.1",
        split="train",
        dest_path=dest,
        allow_synthetic=False,
    )
    assert path.is_file()
    first = _first_line_json(path)
    # The MS MARCO passage dataset contains a ``text`` field.
    assert "text" in first
    assert isinstance(first["text"], str)
    assert first["text"]

def test_fetch_spider_first_row(raw_dir):
    dest = raw_dir / "spider_train.jsonl"
    path = fetch_dataset(
        name="spider",
        config_name=None,
        split="train",
        dest_path=dest,
        allow_synthetic=False,
    )
    assert path.is_file()
    first = _first_line_json(path)
    # Spider examples contain a ``question`` field.
    assert "question" in first
    assert isinstance(first["question"], str)
    assert first["question"]

def test_fetch_dbpedia_ttl_first_line(raw_dir):
    dest = raw_dir / "dbpedia_sample_train.jsonl"
    path = fetch_dataset(
        name="dbpedia_sample",
        config_name=None,
        split="train",
        dest_path=dest,
        allow_synthetic=False,
    )
    assert path.is_file()
    first = _first_line_json(path)
    # Our TTL downloader stores each line under the ``ttl`` key.
    assert "ttl" in first
    assert isinstance(first["ttl"], str)
    assert first["ttl"].strip().startswith("@prefix") or first["ttl"].strip()

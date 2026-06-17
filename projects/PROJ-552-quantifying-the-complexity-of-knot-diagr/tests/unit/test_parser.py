"""
Unit tests for the knot‑atlas parser (T057).

The parser extracts three core invariants from the raw JSON records:
  * crossing number,
  * braid index,
  * hyperbolic volume.
"""

import json
from pathlib import Path

import pytest

from data.parser import parse_knot_atlas_data, ParsedKnotData

# Minimal example record with the required fields.
EXAMPLE_RECORD = {
    "name": "4_1",
    "crossing_number": 4,
    "braid_index": 3,
    "volume": 2.02988,
}

def test_crossing_number_parsing(tmp_path: Path):
    raw = tmp_path / "raw.json"
    raw.write_text(json.dumps([EXAMPLE_RECORD]))
    parsed = parse_knot_atlas_data(raw_path=raw, cleaned_path=tmp_path / "cleaned.csv")
    assert isinstance(parsed, ParsedKnotData)
    assert parsed.crossing_numbers == [4]

def test_braid_index_parsing(tmp_path: Path):
    raw = tmp_path / "raw.json"
    raw.write_text(json.dumps([EXAMPLE_RECORD]))
    parsed = parse_knot_atlas_data(raw_path=raw, cleaned_path=tmp_path / "cleaned.csv")
    assert parsed.braid_indices == [3]

def test_hyperbolic_volume_parsing(tmp_path: Path):
    raw = tmp_path / "raw.json"
    raw.write_text(json.dumps([EXAMPLE_RECORD]))
    parsed = parse_knot_atlas_data(raw_path=raw, cleaned_path=tmp_path / "cleaned.csv")
    assert parsed.volumes == [2.02988]

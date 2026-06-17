"""Unit tests for the KnotAtlas parser."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from code.data.parser import (
    ParsedKnotData,
    parse_knot_atlas_data,
    write_parsed_to_csv,
)


@pytest.fixture
def raw_json(tmp_path: Path):
    """Create a temporary raw JSON file with a header row and two data rows."""
    data = [
        {
            "name": "Header",
            "crossing_number": "Crossing Number",
            "braid_index": "Braid Index",
            "volume": "Volume",
            "alternating": "Alternating",
        },
        {
            "name": "3_1",
            "crossing_number": 3,
            "braid_index": 2,
            "volume": 2.02988,
            "alternating": True,
        },
        {
            "name": "4_1",
            "crossing_number": 4,
            "braid_index": 3,
            "volume": 3.66386,
            "alternating": True,
        },
    ]
    path = tmp_path / "raw.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


def test_parse_knot_atlas_data_skips_header(raw_json: Path):
    """The parser should ignore the header row and return only real records."""
    parsed = parse_knot_atlas_data(raw_json)
    assert isinstance(parsed, list)
    assert len(parsed) == 2
    names = [p.name for p in parsed]
    assert "3_1" in names and "4_1" in names


def test_parsed_knot_data_fields():
    raw = {
        "name": "5_2",
        "crossing_number": 5,
        "braid_index": 3,
        "volume": 1.234,
        "alternating": False,
    }
    parsed = ParsedKnotData.from_raw(raw)
    assert parsed.name == "5_2"
    assert parsed.crossing_number == 5
    assert parsed.braid_index == 3
    assert parsed.volume == 1.234
    assert parsed.alternating is False


def test_write_parsed_to_csv(tmp_path: Path):
    """The CSV writer should produce a file that can be read back with ``csv.DictReader``."""
    records = [
        ParsedKnotData(
            name="6_1",
            crossing_number=6,
            braid_index=4,
            volume=4.123,
            alternating=True,
        )
    ]
    out_csv = tmp_path / "knots.csv"
    write_parsed_to_csv(records, out_csv)

    # Verify file exists and contains a header + one data row
    assert out_csv.is_file()
    with out_csv.open("r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    assert lines[0] == "name,crossing_number,braid_index,volume,alternating"
    assert "6_1" in lines[1]
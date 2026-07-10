"""
Unit tests for code/extraction/parser.py
"""
import json
import csv
import tempfile
from pathlib import Path
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.extraction.parser import parse_row, parse_csv_file, parse_json_file, _find_proximity_match


class TestParseRow:
    def test_extract_quantitative_direct(self):
        """Test direct extraction of r and n."""
        row = {"r": 0.45, "n": 120, "author": "Smith"}
        result = parse_row(row)
        assert result["r"] == 0.45
        assert result["n"] == 120
        assert result["quantitative_available"] is True

    def test_extract_quantitative_string(self):
        """Test extraction from string values."""
        row = {"r": "0.32", "n": "85", "author": "Jones"}
        result = parse_row(row)
        assert result["r"] == 0.32
        assert result["n"] == 85
        assert result["quantitative_available"] is True

    def test_extract_quantitative_missing(self):
        """Test when r or n is missing."""
        row = {"r": 0.45, "author": "Doe"}
        result = parse_row(row)
        assert result["r"] == 0.45
        assert result["n"] is None
        assert result["quantitative_available"] is False

    def test_qualitative_specific_tract_found(self):
        """Test detection of specific tract near directional verb."""
        row = {
            "abstract": "The arcuate fasciculus showed increased connectivity in music lovers.",
            "author": "Test"
        }
        result = parse_row(row)
        assert result["qualitative_descriptor"]["tract"] == "arcuate fasciculus"
        assert result["qualitative_descriptor"]["context"] == "specific_circuitry_found"

    def test_qualitative_no_tract_no_music(self):
        """Test fallback when no tract or music context found."""
        row = {
            "abstract": "General brain activity was measured.",
            "author": "Test"
        }
        result = parse_row(row)
        assert result["qualitative_descriptor"]["no_qualitative_data"] is True

    def test_qualitative_music_only_no_tract(self):
        """Test when music preference is mentioned but no specific tract."""
        row = {
            "abstract": "Participants reported their music preference, and general brain scans were done.",
            "author": "Test"
        }
        result = parse_row(row)
        assert result["qualitative_descriptor"]["no_qualitative_data"] is True
        assert result["qualitative_descriptor"]["context"] == "music_preference_only"

    def test_qualitative_uncinate_tract(self):
        """Test detection of uncinate fasciculus."""
        row = {
            "abstract": "A negative correlation was found between uncinate fasciculus integrity and jazz preference.",
            "author": "Test"
        }
        result = parse_row(row)
        assert result["qualitative_descriptor"]["tract"] == "uncinate fasciculus"
        assert result["qualitative_descriptor"]["context"] == "specific_circuitry_found"


class TestParseCSV:
    def test_parse_csv_file(self):
        """Test parsing a CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'r', 'n', 'abstract'])
            writer.writeheader()
            writer.writerow({'id': 'S1', 'r': '0.5', 'n': '100', 'abstract': 'Arcuate increased in music fans.'})
            temp_path = f.name

        try:
            results = parse_csv_file(temp_path)
            assert len(results) == 1
            assert results[0]['r'] == 0.5
            assert results[0]['n'] == 100
            assert results[0]['qualitative_descriptor']['tract'] == 'arcuate'
        finally:
            Path(temp_path).unlink()


class TestParseJSON:
    def test_parse_json_file(self):
        """Test parsing a JSON file."""
        data = [
            {
                "id": "S1",
                "r": 0.6,
                "n": 50,
                "abstract": "Cingulum bundle correlated with classical music preference."
            }
        ]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            results = parse_json_file(temp_path)
            assert len(results) == 1
            assert results[0]['r'] == 0.6
            assert results[0]['n'] == 50
            assert results[0]['qualitative_descriptor']['tract'] == 'cingulum bundle'
        finally:
            Path(temp_path).unlink()


class TestFindProximityMatch:
    def test_match_arcuate(self):
        text = "The study found that the arcuate fasciculus was increased in individuals with high music preference."
        assert _find_proximity_match(text) == "arcuate fasciculus"

    def test_match_cingulum(self):
        text = "Reduced integrity in the cingulum bundle was associated with lower music liking."
        assert _find_proximity_match(text) == "cingulum bundle"

    def test_no_match(self):
        text = "General brain structures were analyzed without specific tract focus."
        assert _find_proximity_match(text) is None

    def test_match_unspecified_tract(self):
        text = "The corpus callosum showed a positive correlation with music enjoyment."
        assert _find_proximity_match(text) == "corpus callosum"

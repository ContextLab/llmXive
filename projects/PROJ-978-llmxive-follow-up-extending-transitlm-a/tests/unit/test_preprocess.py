import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from data.preprocess import (
    filter_cities,
    build_vocabulary,
    apply_vocabulary_filter,
    stratify_routes,
    save_processed_data,
    validate_output,
)
from config import get_env_config


@pytest.fixture
def sample_data():
    """Sample dataset for testing."""
    return [
        {
            "route_id": "r1",
            "city": "Beijing",
            "stations": ["A", "B", "C", "D", "E"],
        },
        {
            "route_id": "r2",
            "city": "Shanghai",
            "stations": ["F", "G", "H"],
        },
        {
            "route_id": "r3",
            "city": "Guangzhou",
            "stations": ["I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X"],
        },
        {
            "route_id": "r4",
            "city": "Shenzhen",
            "stations": ["Y"] * 35,  # Long route
        },
        {
            "route_id": "r5",
            "city": "Chengdu",  # Not in target cities
            "stations": ["Z"],
        },
    ]


class TestFilterCities:
    def test_filter_cities_basic(self, sample_data):
        """Test basic city filtering."""
        filtered = filter_cities(sample_data, ["Beijing", "Shanghai"])
        assert len(filtered) == 2
        cities = [r["city"] for r in filtered]
        assert all(c in ["Beijing", "Shanghai"] for c in cities)

    def test_filter_cities_empty_result(self, sample_data):
        """Test filtering with no matching cities."""
        filtered = filter_cities(sample_data, ["Chengdu"])
        assert len(filtered) == 1

    def test_filter_cities_no_match(self, sample_data):
        """Test filtering with no matching cities at all."""
        filtered = filter_cities(sample_data, ["NonExistent"])
        assert len(filtered) == 0

    def test_filter_cities_all_match(self, sample_data):
        """Test filtering with all cities matching."""
        filtered = filter_cities(sample_data, ["Beijing", "Shanghai", "Guangzhou", "Shenzhen"])
        assert len(filtered) == 4


class TestBuildVocabulary:
    def test_build_vocabulary_basic(self, sample_data):
        """Test basic vocabulary building."""
        vocab = build_vocabulary(sample_data)
        assert "<UNKNOWN>" in vocab
        assert len(vocab) > 1

    def test_build_vocabulary_top_n(self, sample_data):
        """Test vocabulary building with top_n limit."""
        vocab = build_vocabulary(sample_data, top_n=3)
        assert len(vocab) == 4  # 3 stations + <UNKNOWN>

    def test_build_vocabulary_empty_data(self):
        """Test vocabulary building with empty data."""
        vocab = build_vocabulary([])
        assert "<UNKNOWN>" in vocab
        assert len(vocab) == 1


class TestApplyVocabularyFilter:
    def test_apply_vocabulary_filter_basic(self, sample_data):
        """Test basic vocabulary filtering."""
        vocab = build_vocabulary(sample_data, top_n=3)
        filtered = apply_vocabulary_filter(sample_data, vocab)
        
        # Check that unknown tokens are present
        has_unknown = False
        for record in filtered:
            stations = record.get("stations", [])
            if "<UNKNOWN>" in stations:
                has_unknown = True
                break
        
        assert has_unknown

    def test_apply_vocabulary_filter_no_unknown(self, sample_data):
        """Test vocabulary filtering with full vocabulary."""
        vocab = build_vocabulary(sample_data)  # No top_n limit
        filtered = apply_vocabulary_filter(sample_data, vocab)
        
        # No unknown tokens should be present
        for record in filtered:
            stations = record.get("stations", [])
            assert "<UNKNOWN>" not in stations


class TestStratifyRoutes:
    def test_stratify_routes_basic(self, sample_data):
        """Test basic route stratification."""
        short, medium, long = stratify_routes(sample_data)
        
        assert len(short) == 2  # r1 (5), r2 (3)
        assert len(medium) == 1  # r3 (16)
        assert len(long) == 1  # r4 (35)

    def test_stratify_routes_empty(self):
        """Test stratification with empty data."""
        short, medium, long = stratify_routes([])
        assert len(short) == 0
        assert len(medium) == 0
        assert len(long) == 0


class TestSaveProcessedData:
    def test_save_processed_data_jsonl(self, sample_data):
        """Test saving data in JSONL format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.jsonl"
            save_processed_data(sample_data, str(output_path), file_format="jsonl")
            
            assert output_path.exists()
            assert output_path.stat().st_size > 0
            
            with open(output_path, "r") as f:
                lines = f.readlines()
            assert len(lines) == len(sample_data)

    def test_save_processed_data_json(self, sample_data):
        """Test saving data in JSON format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.json"
            save_processed_data(sample_data, str(output_path), file_format="json")
            
            assert output_path.exists()
            assert output_path.stat().st_size > 0
            
            with open(output_path, "r") as f:
                data = json.load(f)
            assert len(data) == len(sample_data)


class TestValidateOutput:
    def test_validate_output_exists_and_nonempty(self):
        """Test validation of existing non-empty file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.jsonl"
            output_path.write_text('{"test": "data"}\n')
            
            assert validate_output(str(output_path)) is True

    def test_validate_output_not_exists(self):
        """Test validation of non-existent file."""
        assert validate_output("/nonexistent/path/file.jsonl") is False

    def test_validate_output_empty(self):
        """Test validation of empty file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.jsonl"
            output_path.write_text("")
            
            assert validate_output(str(output_path)) is False

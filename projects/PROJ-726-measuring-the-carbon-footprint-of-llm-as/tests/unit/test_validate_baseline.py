"""
Unit tests for T006: validate_baseline.py
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# We need to import the functions from the module.
# Since the module is in code/, we add it to sys.path for testing.
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from validate_baseline import (
    load_json_file,
    load_prompt_ids,
    load_paper_baseline,
    synthesize_baseline,
    validate_schema,
    save_baseline,
    DEFAULT_TIME_MINUTES,
    MIN_TIME_MINUTES,
    MAX_TIME_MINUTES
)


class TestLoadJsonFile:
    def test_load_existing_json(self, tmp_path):
        file_path = tmp_path / "test.json"
        data = {"key": "value"}
        with open(file_path, "w") as f:
            json.dump(data, f)

        result = load_json_file(file_path)
        assert result == data

    def test_load_non_existing_json(self, tmp_path):
        file_path = tmp_path / "non_existing.json"
        result = load_json_file(file_path)
        assert result is None

    def test_load_invalid_json(self, tmp_path):
        file_path = tmp_path / "invalid.json"
        with open(file_path, "w") as f:
            f.write("not valid json")

        result = load_json_file(file_path)
        assert result is None


class TestSynthesizeBaseline:
    def test_synthesize_baseline_creates_dict(self):
        prompt_ids = ["p1", "p2", "p3"]
        result = synthesize_baseline(prompt_ids)

        assert isinstance(result, dict)
        assert len(result) == 3
        for pid, time_val in result.items():
            assert pid in prompt_ids
            assert time_val == DEFAULT_TIME_MINUTES

    def test_synthesize_baseline_empty_list(self):
        result = synthesize_baseline([])
        assert result == {}


class TestValidateSchema:
    def test_valid_schema(self):
        data = {"p1": 30.0, "p2": 45.5}
        assert validate_schema(data) is True

    def test_invalid_non_dict(self):
        assert validate_schema([]) is False
        assert validate_schema("string") is False

    def test_invalid_non_string_key(self):
        data = {123: 30.0}
        assert validate_schema(data) is False

    def test_invalid_non_numeric_value(self):
        data = {"p1": "thirty"}
        assert validate_schema(data) is False

    def test_invalid_negative_value(self):
        data = {"p1": -10.0}
        assert validate_schema(data) is False

class TestLoadPaperBaseline:
    def test_load_valid_paper_data(self, tmp_path):
        # Create a mock paper data file
        file_path = tmp_path / "paper_data.json"
        data = {"p1": 30.0, "p2": 45.0, "p3": 60.0}
        with open(file_path, "w") as f:
            json.dump(data, f)

        with patch("validate_baseline.PAPER_DATA_FILE", file_path):
            result = load_paper_baseline()

        assert result == data

    def test_load_empty_paper_data(self, tmp_path):
        file_path = tmp_path / "paper_data.json"
        data = {}
        with open(file_path, "w") as f:
            json.dump(data, f)

        with patch("validate_baseline.PAPER_DATA_FILE", file_path):
            result = load_paper_baseline()

        assert result is None

    def test_load_missing_paper_data(self):
        with patch("validate_baseline.PAPER_DATA_FILE", Path("/non/existent/path.json")):
            result = load_paper_baseline()
        assert result is None
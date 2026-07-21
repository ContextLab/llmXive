import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import torch

from src.generation.generation import write_jsonl, write_labeled_dataset, label_validity, GenerationConfig
from src.utils.validators import validate_token_sequence, validate_validity_label

class TestWriteJsonl:
    def test_write_jsonl_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.jsonl"
            records = [
                {"prompt_id": "1", "tokens": [1, 2, 3], "validity": True, "entropy": 0.5},
                {"prompt_id": "2", "tokens": [4, 5], "validity": False, "entropy": 0.2}
            ]
            
            write_jsonl(records, str(output_path))
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                lines = f.readlines()
            assert len(lines) == 2
            assert json.loads(lines[0])["prompt_id"] == "1"
            assert json.loads(lines[1])["validity"] == False

    def test_write_jsonl_empty_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "empty.jsonl"
            write_jsonl([], str(output_path))
            assert output_path.exists()
            with open(output_path, 'r') as f:
                assert f.read() == ""

    def test_write_jsonl_with_validation(self):
        def dummy_validator(record):
            if "invalid_key" in record:
                raise ValueError("Invalid key found")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "valid.jsonl"
            records = [
                {"prompt_id": "1", "tokens": [1, 2], "validity": True, "entropy": 0.0},
                {"invalid_key": "bad"}
            ]
            
            # Should skip the invalid record
            write_jsonl(records, str(output_path), schema_validator=dummy_validator)
            
            with open(output_path, 'r') as f:
                lines = f.readlines()
            # Only the valid record should be written
            assert len(lines) == 1
            assert json.loads(lines[0])["prompt_id"] == "1"

class TestWriteLabeledDataset:
    def test_write_labeled_dataset_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "labeled.jsonl"
            results = [
                ("p1", [10, 20], True, 0.1),
                ("p2", [30, 40, 50], False, 0.9)
            ]
            
            write_labeled_dataset(results, str(output_path))
            
            with open(output_path, 'r') as f:
                line1 = json.loads(f.readline())
                line2 = json.loads(f.readline())
            
            assert line1["prompt_id"] == "p1"
            assert line1["tokens"] == [10, 20]
            assert line1["validity"] is True
            assert line1["entropy"] == 0.1
            
            assert line2["prompt_id"] == "p2"
            assert line2["validity"] is False

class TestLabelValidity:
    def test_label_validity_match(self):
        generated = [1, 2, 3]
        ground_truth = [[1, 2, 3], [4, 5, 6]]
        assert label_validity(generated, ground_truth, "test_id") is True

    def test_label_validity_no_match(self):
        generated = [1, 2, 4]
        ground_truth = [[1, 2, 3], [4, 5, 6]]
        # This should log a warning but return False
        assert label_validity(generated, ground_truth, "test_id") is False

    def test_label_validity_empty_ground_truth(self):
        generated = [1, 2]
        assert label_validity(generated, [], "test_id") is False

class TestGenerationConfig:
    def test_generation_config_defaults(self):
        config = GenerationConfig(model_path="test")
        assert config.temperature == 0.0
        assert config.do_sample is False
        assert config.max_new_tokens == 128
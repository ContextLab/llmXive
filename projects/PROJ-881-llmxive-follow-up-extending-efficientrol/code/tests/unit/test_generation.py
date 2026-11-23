import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import torch

from src.generation.generation import (
    GenerationConfig,
    generate_baseline,
    write_jsonl,
    write_labeled_dataset,
    label_validity
)


class TestGenerationConfig:
    """Tests for GenerationConfig class."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        config = GenerationConfig()
        assert config.model_name == "distilgpt2"
        assert config.max_new_tokens == 100
        assert config.temperature == 0.0
        assert config.do_sample is False

    def test_temperature_forces_deterministic(self):
        """Test that temperature=0.0 forces do_sample=False."""
        config = GenerationConfig(temperature=0.0, do_sample=True)
        # The constructor should set do_sample to False when temperature is 0.0
        assert config.temperature == 0.0
        assert config.do_sample is False

    def test_custom_values(self):
        """Test that custom values are set correctly."""
        config = GenerationConfig(
            model_name="test-model",
            max_new_tokens=200,
            temperature=0.7,
            do_sample=True
        )
        assert config.model_name == "test-model"
        assert config.max_new_tokens == 200
        assert config.temperature == 0.7
        assert config.do_sample is True


class TestWriteJsonl:
    """Tests for write_jsonl function."""

    def test_write_single_record(self):
        """Test writing a single record to JSONL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.jsonl"
            data = [{"key": "value", "number": 123}]
            
            write_jsonl(data, str(output_path))
            
            assert output_path.exists()
            with open(output_path, "r") as f:
                lines = f.readlines()
            assert len(lines) == 1
            record = json.loads(lines[0])
            assert record["key"] == "value"
            assert record["number"] == 123

    def test_write_multiple_records(self):
        """Test writing multiple records to JSONL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.jsonl"
            data = [
                {"id": 1, "text": "first"},
                {"id": 2, "text": "second"},
                {"id": 3, "text": "third"}
            ]
            
            write_jsonl(data, str(output_path))
            
            assert output_path.exists()
            with open(output_path, "r") as f:
                lines = f.readlines()
            assert len(lines) == 3
            for i, line in enumerate(lines):
                record = json.loads(line)
                assert record["id"] == i + 1

    def test_creates_directory(self):
        """Test that write_jsonl creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "nested" / "test.jsonl"
            data = [{"test": "data"}]
            
            write_jsonl(data, str(output_path))
            
            assert output_path.exists()


class TestWriteLabeledDataset:
    """Tests for write_labeled_dataset function."""

    def test_write_labeled_data(self):
        """Test writing labeled dataset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "labeled.jsonl"
            data = [
                {"prompt_id": "1", "validity": True},
                {"prompt_id": "2", "validity": False}
            ]
            
            write_labeled_dataset(data, str(output_path), logger=Mock())
            
            assert output_path.exists()
            with open(output_path, "r") as f:
                lines = f.readlines()
            assert len(lines) == 2


class TestLabelValidity:
    """Tests for label_validity function."""

    def test_label_validity_returns_list(self):
        """Test that label_validity returns a list."""
        generation_data = [{"prompt": "test"}]
        ground_truth = {}
        
        result = label_validity(generation_data, ground_truth, logger=Mock())
        
        assert isinstance(result, list)
        assert len(result) == 1

    def test_label_validity_adds_validity_key(self):
        """Test that label_validity adds validity key to items."""
        generation_data = [{"prompt": "test", "prompt_id": "1"}]
        ground_truth = {}
        
        result = label_validity(generation_data, ground_truth, logger=Mock())
        
        assert "validity" in result[0]
        assert result[0]["validity"] is None  # Placeholder value

    def test_label_validity_preserves_input(self):
        """Test that label_validity preserves original data."""
        generation_data = [
            {"prompt": "test1", "prompt_id": "1", "extra": "data"},
            {"prompt": "test2", "prompt_id": "2", "extra": "more"}
        ]
        ground_truth = {}
        
        result = label_validity(generation_data, ground_truth, logger=Mock())
        
        assert result[0]["prompt"] == "test1"
        assert result[0]["prompt_id"] == "1"
        assert result[0]["extra"] == "data"
        assert result[1]["prompt"] == "test2"
        assert result[1]["prompt_id"] == "2"
        assert result[1]["extra"] == "more"


class TestGenerateBaseline:
    """Tests for generate_baseline function (mocked)."""

    @patch('src.generation.generation.generate_single_pass')
    def test_generate_baseline_calls_single_pass(self, mock_single_pass):
        """Test that generate_baseline calls generate_single_pass for each prompt."""
        mock_model = Mock()
        mock_tokenizer = Mock()
        mock_config = GenerationConfig(temperature=0.0)
        mock_logger = Mock()
        
        # Mock the return value
        mock_single_pass.return_value = {
            "prompt": "test",
            "generated_text": "response",
            "generated_ids": [1, 2, 3],
            "input_length": 5,
            "generated_length": 3
        }
        
        prompts = ["prompt1", "prompt2"]
        result = generate_baseline(
            model=mock_model,
            tokenizer=mock_tokenizer,
            prompts=prompts,
            config=mock_config,
            logger=mock_logger,
            device="cpu"
        )
        
        assert mock_single_pass.call_count == 2
        assert len(result) == 2

    @patch('src.generation.generation.generate_single_pass')
    def test_generate_baseline_adds_prompt_id(self, mock_single_pass):
        """Test that generate_baseline adds prompt_id to results."""
        mock_model = Mock()
        mock_tokenizer = Mock()
        mock_config = GenerationConfig(temperature=0.0)
        mock_logger = Mock()
        
        mock_single_pass.return_value = {
            "prompt": "test",
            "generated_text": "response",
            "generated_ids": [1, 2, 3],
            "input_length": 5,
            "generated_length": 3
        }
        
        prompts = ["prompt1"]
        result = generate_baseline(
            model=mock_model,
            tokenizer=mock_tokenizer,
            prompts=prompts,
            config=mock_config,
            logger=mock_logger,
            device="cpu"
        )
        
        assert "prompt_id" in result[0]
        assert result[0]["prompt_id"].startswith("prompt_")

    @patch('src.generation.generation.generate_single_pass')
    def test_generate_baseline_writes_to_file(self, mock_single_pass):
        """Test that generate_baseline writes to file when output_file is provided."""
        mock_model = Mock()
        mock_tokenizer = Mock()
        mock_config = GenerationConfig(temperature=0.0)
        mock_logger = Mock()
        
        mock_single_pass.return_value = {
            "prompt": "test",
            "generated_text": "response",
            "generated_ids": [1, 2, 3],
            "input_length": 5,
            "generated_length": 3
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "output.jsonl"
            prompts = ["prompt1"]
            
            result = generate_baseline(
                model=mock_model,
                tokenizer=mock_tokenizer,
                prompts=prompts,
                config=mock_config,
                logger=mock_logger,
                device="cpu",
                output_file=str(output_file)
            )
            
            assert output_file.exists()
            with open(output_file, "r") as f:
                lines = f.readlines()
            assert len(lines) == 1

    @patch('src.generation.generation.generate_single_pass')
    def test_generate_baseline_handles_errors(self, mock_single_pass):
        """Test that generate_baseline handles errors gracefully."""
        mock_model = Mock()
        mock_tokenizer = Mock()
        mock_config = GenerationConfig(temperature=0.0)
        mock_logger = Mock()
        
        # First call succeeds, second fails
        mock_single_pass.side_effect = [
            {
                "prompt": "test",
                "generated_text": "response",
                "generated_ids": [1, 2, 3],
                "input_length": 5,
                "generated_length": 3
            },
            Exception("Generation failed")
        ]
        
        prompts = ["prompt1", "prompt2"]
        result = generate_baseline(
            model=mock_model,
            tokenizer=mock_tokenizer,
            prompts=prompts,
            config=mock_config,
            logger=mock_logger,
            device="cpu"
        )
        
        # Should return results for both, with error info for the second
        assert len(result) == 2
        assert "error" in result[1]
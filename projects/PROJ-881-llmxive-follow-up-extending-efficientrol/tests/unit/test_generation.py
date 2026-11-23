import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import torch
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.generation.generation import (
    GenerationConfig,
    label_validity,
    write_jsonl,
    write_labeled_dataset,
    setup_logging
)

class TestLabelValidity:
    """Tests for ground truth matching logic."""
    
    def test_gsm8k_exact_match(self):
        """Test GSM8K validity labeling with exact answer match."""
        generated_sequences = [
            {
                "prompt_id": "gsm8k_001",
                "generated_text": "Step 1: 5 + 3 = 8\n#### 8",
                "original_example": {
                    "dataset": "gsm8k",
                    "answer": "8"
                }
            }
        ]
        
        dataset = [
            {"id": "gsm8k_001", "dataset": "gsm8k", "answer": "8"}
        ]
        
        logger = setup_logging()
        labeled = label_validity(generated_sequences, dataset, logger)
        
        assert len(labeled) == 1
        assert labeled[0]["validity"] is True
        assert labeled[0]["validity_label"]["reason"] == "match"
    
    def test_gsm8k_no_match(self):
        """Test GSM8K validity labeling when answer doesn't match."""
        generated_sequences = [
            {
                "prompt_id": "gsm8k_002",
                "generated_text": "Step 1: 5 + 3 = 7\n#### 7",
                "original_example": {
                    "dataset": "gsm8k",
                    "answer": "8"
                }
            }
        ]
        
        dataset = [
            {"id": "gsm8k_002", "dataset": "gsm8k", "answer": "8"}
        ]
        
        logger = setup_logging()
        labeled = label_validity(generated_sequences, dataset, logger)
        
        assert len(labeled) == 1
        assert labeled[0]["validity"] is False
        assert labeled[0]["validity_label"]["reason"] == "no_match"
    
    def test_minigrid_multiple_valid_paths(self):
        """Test MiniGrid validity labeling with multiple valid paths."""
        generated_sequences = [
            {
                "prompt_id": "minigrid_001",
                "generated_text": "forward turn_right forward",
                "original_example": {
                    "dataset": "minigrid",
                    "valid_paths": [
                        "forward forward turn_right",
                        "forward turn_right forward"
                    ]
                }
            }
        ]
        
        dataset = [
            {
                "id": "minigrid_001",
                "dataset": "minigrid",
                "valid_paths": [
                    "forward forward turn_right",
                    "forward turn_right forward"
                ]
            }
        ]
        
        logger = setup_logging()
        labeled = label_validity(generated_sequences, dataset, logger)
        
        assert len(labeled) == 1
        assert labeled[0]["validity"] is True
        assert labeled[0]["validity_label"]["reason"] == "match"
    
    def test_minigrid_no_valid_path(self):
        """Test MiniGrid when generated path doesn't match any valid path."""
        generated_sequences = [
            {
                "prompt_id": "minigrid_002",
                "generated_text": "backward turn_left",
                "original_example": {
                    "dataset": "minigrid",
                    "valid_paths": [
                        "forward turn_right",
                        "forward forward"
                    ]
                }
            }
        ]
        
        dataset = [
            {
                "id": "minigrid_002",
                "dataset": "minigrid",
                "valid_paths": [
                    "forward turn_right",
                    "forward forward"
                ]
            }
        ]
        
        logger = setup_logging()
        labeled = label_validity(generated_sequences, dataset, logger)
        
        assert len(labeled) == 1
        assert labeled[0]["validity"] is False
        assert labeled[0]["validity_label"]["reason"] == "no_match"
    
    def test_no_match_logs_warning(self, caplog):
        """Test that no-match cases are logged."""
        generated_sequences = [
            {
                "prompt_id": "test_001",
                "generated_text": "wrong answer",
                "original_example": {
                    "dataset": "gsm8k",
                    "answer": "correct"
                }
            }
        ]
        
        dataset = [
            {"id": "test_001", "dataset": "gsm8k", "answer": "correct"}
        ]
        
        logger = setup_logging()
        labeled = label_validity(generated_sequences, dataset, logger)
        
        # Verify validity is false
        assert labeled[0]["validity"] is False

class TestWriteJsonl:
    """Tests for JSONL writing functionality."""
    
    def test_write_jsonl_creates_file(self):
        """Test that write_jsonl creates the output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.jsonl"
            data = [
                {"prompt_id": "test1", "tokens": ["a", "b"], "validity": True},
                {"prompt_id": "test2", "tokens": ["c", "d"], "validity": False}
            ]
            
            logger = setup_logging()
            write_jsonl(data, str(output_path), logger)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 2
    
    def test_write_jsonl_valid_format(self):
        """Test that written JSONL is valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.jsonl"
            data = [
                {"prompt_id": "test1", "tokens": ["a", "b"], "validity": True}
            ]
            
            logger = setup_logging()
            write_jsonl(data, str(output_path), logger)
            
            with open(output_path, 'r') as f:
                for line in f:
                    parsed = json.loads(line)
                    assert "prompt_id" in parsed
                    assert "tokens" in parsed
                    assert "validity" in parsed

class TestWriteLabeledDataset:
    """Tests for labeled dataset writing."""
    
    def test_standardizes_fields(self):
        """Test that write_labeled_dataset standardizes record fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "labeled.jsonl"
            labeled_data = [
                {
                    "prompt_id": "test1",
                    "tokens": ["a", "b"],
                    "validity": True,
                    "validity_label": {
                        "ground_truth": "expected",
                        "reason": "match"
                    }
                }
            ]
            
            logger = setup_logging()
            write_labeled_dataset(labeled_data, str(output_path), logger)
            
            with open(output_path, 'r') as f:
                record = json.loads(f.readline())
                assert "prompt_id" in record
                assert "tokens" in record
                assert "validity" in record
                assert "ground_truth" in record
                assert "reason" in record

class TestGenerationConfig:
    """Tests for GenerationConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = GenerationConfig()
        assert config.temperature == 0.0
        assert config.max_new_tokens == 128
        assert config.batch_size == 1
        assert config.seed == 42
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = GenerationConfig(
            model_name="test-model",
            temperature=0.7,
            max_new_tokens=256
        )
        assert config.model_name == "test-model"
        assert config.temperature == 0.7
        assert config.max_new_tokens == 256
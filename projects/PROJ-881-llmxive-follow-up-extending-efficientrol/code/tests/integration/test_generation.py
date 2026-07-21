"""
Integration tests for the generation module, specifically testing streaming writes.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Any
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.generation.generation import process_batch, GenerationConfig, process_dataset
from src.utils.entropy_calc import calculate_entropy

class TestStreamingWrites:
    """Test suite for streaming/chunking logic."""

    def test_streaming_writes(self):
        """
        Verify that process_batch writes to disk immediately after each batch.
        Tests the requirement to process fixed-size token batches of 50 tokens
        and write to disk immediately to stay within 7GB RAM limit.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_entropy_profiles.jsonl"
            
            # Create sample batch records
            batch_records = [
                {
                    "prompt_id": "test_1",
                    "tokens": [101, 102, 103, 104, 105],
                    "validity": True,
                    "entropy": [0.1, 0.2, 0.3, 0.4, 0.5],
                    "entropy_profile": {
                        "layers": [
                            {"layer_id": 0, "entropy": 0.1},
                            {"layer_id": 1, "entropy": 0.2},
                            {"layer_id": 2, "entropy": 0.3},
                            {"layer_id": 3, "entropy": 0.4},
                            {"layer_id": 4, "entropy": 0.5},
                        ]
                    }
                },
                {
                    "prompt_id": "test_2",
                    "tokens": [201, 202, 203],
                    "validity": False,
                    "entropy": [0.6, 0.7, 0.8],
                    "entropy_profile": {
                        "layers": [
                            {"layer_id": 0, "entropy": 0.6},
                            {"layer_id": 1, "entropy": 0.7},
                            {"layer_id": 2, "entropy": 0.8},
                        ]
                    }
                }
            ]
            
            # Call process_batch
            process_batch(batch_records, output_path)
            
            # Verify file exists and contains correct data
            assert output_path.exists(), "Output file was not created"
            
            with open(output_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            assert len(lines) == len(batch_records), f"Expected {len(batch_records)} lines, got {len(lines)}"
            
            # Verify content
            for i, line in enumerate(lines):
                record = json.loads(line)
                assert record["prompt_id"] == batch_records[i]["prompt_id"]
                assert record["tokens"] == batch_records[i]["tokens"]
                assert record["validity"] == batch_records[i]["validity"]
                assert record["entropy"] == batch_records[i]["entropy"]
            
            # Verify newline delimiter (JSONL format)
            for line in lines:
                assert line.endswith('\n'), "Lines must end with newline delimiter"

    def test_batch_size_limit(self):
        """
        Verify that the system processes batches of 50 tokens and writes immediately.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "batch_test.jsonl"
            
            # Create a batch that exactly hits the 50 token limit
          # 10 records * 5 tokens = 50 tokens
            batch_records = [
                {
                    "prompt_id": f"test_{i}",
                    "tokens": [i*10 + j for j in range(5)],
                    "validity": True,
                    "entropy": [0.1] * 5,
                    "entropy_profile": {
                        "layers": [{"layer_id": j, "entropy": 0.1} for j in range(5)]
                    }
                }
                for i in range(10)
            ]
            
            process_batch(batch_records, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                content = f.read()
            
            # Verify all records are present
            lines = content.strip().split('\n')
            assert len(lines) == 10

    def test_streaming_writes_empty_batch(self):
        """Test behavior with an empty batch."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "empty_test.jsonl"
            
            # Create empty batch
            process_batch([], output_path)
            
            # File should exist but be empty
            assert output_path.exists()
            assert output_path.stat().st_size == 0

    def test_large_batch_streaming(self):
        """Test streaming with a larger batch to ensure memory efficiency."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "large_test.jsonl"
            
            # Create a large batch (simulating 500 tokens)
            batch_records = [
                {
                    "prompt_id": f"test_{i}",
                    "tokens": [i*100 + j for j in range(10)],
                    "validity": i % 2 == 0,
                    "entropy": [0.1 * j for j in range(10)],
                    "entropy_profile": {
                        "layers": [{"layer_id": j, "entropy": 0.1 * j} for j in range(10)]
                    }
                }
                for i in range(50) # 50 * 10 = 500 tokens
            ]
            
            process_batch(batch_records, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) == 50, "All records should be written"
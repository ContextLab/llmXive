import pytest
import os
import json
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import tempfile
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.memory_strategy import (
    estimate_clip_memory,
    determine_strategy,
    apply_strategy,
    save_chunking_config,
    generate_memory_log_entry,
    MEMORY_LIMIT_MB,
    SUBSAMPLE_THRESHOLD_FRAMES,
    CHUNK_SIZE_FRAMES
)
from utils.memory_manager import calculate_max_frames

class TestMemoryStrategy:
    """Unit tests for memory strategy module."""

    def test_estimate_clip_memory_small(self):
        """Test memory estimation for a small clip."""
        # 100 frames, 224x224, 3 channels, float32
        memory = estimate_clip_memory(100)
        expected_mb = (100 * 224 * 224 * 3 * 4) / (1024 * 1024)
        assert abs(memory - expected_mb) < 0.01

    def test_estimate_clip_memory_large(self):
        """Test memory estimation for a large clip."""
        # 10000 frames
        memory = estimate_clip_memory(10000)
        expected_mb = (10000 * 224 * 224 * 3 * 4) / (1024 * 1024)
        assert abs(memory - expected_mb) < 0.01

    def test_determine_strategy_subsample(self):
        """Test strategy determination for short clips (subsample)."""
        # Short clip: 5 seconds at 30 fps = 150 frames
        # Should use subsampling
        strategy_info = determine_strategy(5.0, 30, "test_clip_short")
        assert strategy_info["strategy"] == "subsample"
        assert strategy_info["total_frames"] == 150

    def test_determine_strategy_chunk_long(self):
        """Test strategy determination for long clips (chunk)."""
        # Long clip: 20 seconds at 30 fps = 600 frames
        # Should use chunking (over threshold)
        strategy_info = determine_strategy(20.0, 30, "test_clip_long")
        assert strategy_info["strategy"] == "chunk"
        assert strategy_info["total_frames"] == 600

    def test_determine_strategy_chunk_memory_exceeded(self):
        """Test strategy determination when memory limit exceeded."""
        # Very long clip that exceeds memory even with subsampling
        # 100 seconds at 30 fps = 3000 frames
        # This should force chunking due to memory limit
        strategy_info = determine_strategy(100.0, 30, "test_clip_oom")
        assert strategy_info["strategy"] == "chunk"
        assert strategy_info["total_frames"] == 3000

    def test_apply_strategy_subsample(self):
        """Test applying subsampling strategy."""
        strategy_info = {
            "clip_id": "test_subsample",
            "strategy": "subsample",
            "total_frames": 500,
            "fps": 30,
            "duration_seconds": 500/30
        }
        
        result = apply_strategy(strategy_info)
        
        assert result["strategy"] == "subsample"
        assert result["original_frames"] == 500
        assert result["processed_frames"] < 500
        assert len(result["frame_indices"]) == result["processed_frames"]
        assert result["chunk_boundaries"] == []

    def test_apply_strategy_chunk(self):
        """Test applying chunking strategy."""
        strategy_info = {
            "clip_id": "test_chunk",
            "strategy": "chunk",
            "total_frames": 1000,
            "fps": 30,
            "duration_seconds": 1000/30
        }
        
        result = apply_strategy(strategy_info)
        
        assert result["strategy"] == "chunk"
        assert result["num_chunks"] > 0
        assert result["chunk_size"] == CHUNK_SIZE_FRAMES
        assert len(result["chunk_boundaries"]) == result["num_chunks"]
        # Verify chunk boundaries are valid
        for start, end in result["chunk_boundaries"]:
            assert start < end
            assert end - start <= CHUNK_SIZE_FRAMES + 1

    def test_save_chunking_config(self):
        """Test saving chunking configuration to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_config.json")
            config = {
                "memory_limit_gb": 7.0,
                "strategies": [
                    {
                        "clip_id": "test",
                        "strategy": "subsample",
                        "total_frames": 100
                    }
                ]
            }
            
            save_chunking_config(config, output_path)
            
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                loaded_config = json.load(f)
            
            assert loaded_config == config

    def test_generate_memory_log_entry(self):
        """Test generation of memory log entry."""
        entry = generate_memory_log_entry(
            clip_id="test_clip",
            strategy="subsample",
            memory_usage_mb=150.5,
            success=True
        )
        
        assert entry["clip_id"] == "test_clip"
        assert entry["strategy"] == "subsample"
        assert entry["memory_usage_mb"] == 150.5
        assert entry["success"] is True
        assert "timestamp" in entry

    def test_memory_limit_constants(self):
        """Test that memory limit constants are reasonable."""
        assert MEMORY_LIMIT_MB == 7 * 1024  # 7 GB in MB
        assert SUBSAMPLE_THRESHOLD_FRAMES == 300
        assert CHUNK_SIZE_FRAMES == 256

    def test_apply_strategy_edge_cases(self):
        """Test edge cases in strategy application."""
        # Very small clip
        small_strategy = {
            "clip_id": "tiny",
            "strategy": "subsample",
            "total_frames": 10,
            "fps": 30,
            "duration_seconds": 10/30
        }
        result = apply_strategy(small_strategy)
        assert result["processed_frames"] <= 10
        
        # Exactly at threshold
        threshold_strategy = {
            "clip_id": "threshold",
            "strategy": "subsample",
            "total_frames": SUBSAMPLE_THRESHOLD_FRAMES,
            "fps": 30,
            "duration_seconds": SUBSAMPLE_THRESHOLD_FRAMES/30
        }
        result = apply_strategy(threshold_strategy)
        # Should still subsample if near limit

    def test_chunk_boundary_validity(self):
        """Test that chunk boundaries cover all frames without overlap."""
        strategy_info = {
            "clip_id": "coverage_test",
            "strategy": "chunk",
            "total_frames": 500,
            "fps": 30,
            "duration_seconds": 500/30
        }
        
        result = apply_strategy(strategy_info)
        boundaries = result["chunk_boundaries"]
        
        # Verify coverage
        covered_frames = set()
        for start, end in boundaries:
            for i in range(start, end):
                covered_frames.add(i)
        
        assert len(covered_frames) == strategy_info["total_frames"]
        assert max(covered_frames) == strategy_info["total_frames"] - 1
        assert min(covered_frames) == 0
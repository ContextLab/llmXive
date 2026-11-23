import pytest
import numpy as np
import sys
import os

# Ensure project root is in path
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from utils.memory_manager import (
    estimate_frame_memory,
    calculate_max_frames,
    generate_subsample_indices,
    generate_temporal_chunks,
    get_processing_plan
)

class TestEstimateFrameMemory:
    def test_default_frame_size(self):
        # Default 1920x1080, RGB float32 (3*4 bytes)
        expected = 1920 * 1080 * 12
        assert estimate_frame_memory() == expected

    def test_custom_frame_size(self):
        width, height = 640, 480
        expected = 640 * 480 * 12
        assert estimate_frame_memory(width, height) == expected

class TestCalculateMaxFrames:
    def test_basic_calculation(self):
        # 1GB target, small frame (100x100)
        # 100*100*12 = 120,000 bytes per frame
        # 1GB = 1,073,741,824 bytes
        # Overhead 1.5 -> ~715MB available
        # 715MB / 120KB ~ 5964 frames
        width, height = 100, 100
        target_gb = 1.0
        result = calculate_max_frames(width, height, target_gb)
        assert result > 0
        # Verify mathematically
        frame_mem = width * height * 12
        available = (target_gb * 1024**3) / 1.5
        expected = int(available / frame_mem)
        assert result == expected

    def test_small_target_memory(self):
        # Very small target should still return at least 1
        result = calculate_max_frames(1920, 1080, 0.001) # 1MB
        assert result >= 1

class TestGenerateSubsampleIndices:
    def test_no_subsampling_needed(self):
        total = 10
        max_keep = 20
        indices = generate_subsample_indices(total, max_keep)
        assert indices == list(range(total))

    def test_uniform_subsampling(self):
        total = 100
        max_keep = 10
        indices = generate_subsample_indices(total, max_keep, strategy="uniform")
        assert len(indices) == max_keep
        # Check roughly even spacing
        diffs = np.diff(indices)
        # Should be close to 10
        assert all(8 <= d <= 12 for d in diffs), f"Diffs: {diffs}"

    def test_invalid_strategy(self):
        with pytest.raises(SystemExit): # fail_loudly calls sys.exit
            generate_subsample_indices(100, 10, strategy="invalid")

class TestGenerateTemporalChunks:
    def test_no_overlap(self):
        total = 100
        chunk = 10
        chunks = generate_temporal_chunks(total, chunk, overlap=0)
        assert len(chunks) == 10
        assert chunks[0] == (0, 10)
        assert chunks[-1] == (90, 100)

    def test_with_overlap(self):
        total = 10
        chunk = 4
        overlap = 1
        # Step = 3
        # Chunks: [0,4], [3,7], [6,10]
        chunks = generate_temporal_chunks(total, chunk, overlap)
        assert len(chunks) == 3
        assert chunks[0] == (0, 4)
        assert chunks[1] == (3, 7)
        assert chunks[2] == (6, 10)

    def test_invalid_overlap(self):
        with pytest.raises(SystemExit):
            generate_temporal_chunks(100, 10, overlap=10) # overlap >= chunk

class TestGetProcessingPlan:
    def test_plan_generation(self):
        plan = get_processing_plan(1000, 1920, 1080, 7.0)
        assert "max_frames" in plan
        assert "subsample_indices" in plan
        assert "is_subsampled" in plan
        assert plan["is_subsampled"] is True # 1000 frames likely exceeds 7GB limit for full res
        assert len(plan["subsample_indices"]) <= plan["max_frames"]

    def test_plan_no_subsample(self):
        plan = get_processing_plan(10, 100, 100, 7.0)
        assert plan["is_subsampled"] is False
        assert plan["subsample_indices"] == list(range(10))
import pytest
import numpy as np
from code.utils.memory_manager import (
    estimate_frame_memory,
    calculate_max_frames,
    generate_subsample_indices,
    generate_temporal_chunks,
    get_processing_plan
)

class TestEstimateFrameMemory:
    def test_standard_frame(self):
        # 1920x1080 RGB float32
        mem = estimate_frame_memory(1920, 1080, 3, 'float32')
        expected = 1920 * 1080 * 3 * 4
        assert mem == expected

    def test_small_frame(self):
        mem = estimate_frame_memory(64, 64, 3, 'float32')
        assert mem == 64 * 64 * 3 * 4

    def test_float16(self):
        mem = estimate_frame_memory(100, 100, 3, 'float16')
        assert mem == 100 * 100 * 3 * 2

class TestCalculateMaxFrames:
    def test_basic_calculation(self):
        # 1GB limit, small frames
        max_f = calculate_max_frames(1.0, 100, 100, 3, 'float32', overhead_factor=1.0)
        # 100*100*3*4 = 120,000 bytes per frame
        # 1GB = 1,073,741,824 bytes
        # 1073741824 / 120000 ≈ 8947
        assert max_f > 8000

    def test_with_overhead(self):
        # Same but with 20% overhead
        max_f_no_overhead = calculate_max_frames(1.0, 100, 100, 3, 'float32', overhead_factor=1.0)
        max_f_with_overhead = calculate_max_frames(1.0, 100, 100, 3, 'float32', overhead_factor=1.2)
        assert max_f_with_overhead < max_f_no_overhead
        # Should be roughly 1/1.2 of the no-overhead case
        assert max_f_with_overhead >= int(max_f_no_overhead / 1.3)

    def test_minimum_one_frame(self):
        # Tiny memory limit
        max_f = calculate_max_frames(0.000001, 1000, 1000, 3, 'float32')
        assert max_f >= 1

class TestGenerateSubsampleIndices:
    def test_no_subsampling_needed(self):
        indices = generate_subsample_indices(10, 20)
        assert indices == list(range(10))

    def test_uniform_subsampling(self):
        indices = generate_subsample_indices(100, 10, strategy='uniform')
        assert len(indices) == 10
        # Check roughly uniform distribution
        assert indices[0] == 0
        assert indices[-1] == 99

    def test_random_subsampling(self):
        indices = generate_subsample_indices(100, 10, strategy='random', seed=42)
        assert len(indices) == 10
        assert len(set(indices)) == 10  # No duplicates
        assert all(0 <= i < 100 for i in indices)
        assert indices == sorted(indices)  # Should be sorted

    def test_random_reproducibility(self):
        indices1 = generate_subsample_indices(100, 10, strategy='random', seed=42)
        indices2 = generate_subsample_indices(100, 10, strategy='random', seed=42)
        assert indices1 == indices2

    def test_invalid_strategy(self):
        with pytest.raises(ValueError):
            generate_subsample_indices(100, 10, strategy='invalid')

class TestGenerateTemporalChunks:
    def test_no_overlap(self):
        chunks = generate_temporal_chunks(100, 10, overlap=0)
        assert len(chunks) == 10
        assert chunks[0] == (0, 10)
        assert chunks[1] == (10, 20)
        assert chunks[-1] == (90, 100)

    def test_with_overlap(self):
        chunks = generate_temporal_chunks(100, 10, overlap=2)
        # 100 frames, chunk 10, overlap 2 -> step 8
        # Chunks: (0,10), (8,18), (16,26), ...
        assert len(chunks) > 10
        assert chunks[0] == (0, 10)
        assert chunks[1] == (8, 18)

    def test_partial_last_chunk(self):
        chunks = generate_temporal_chunks(105, 10, overlap=0)
        assert chunks[-1] == (100, 105)

    def test_invalid_params(self):
        with pytest.raises(ValueError):
            generate_temporal_chunks(100, 0)
        with pytest.raises(ValueError):
            generate_temporal_chunks(100, 10, overlap=-1)
        with pytest.raises(ValueError):
            generate_temporal_chunks(100, 10, overlap=10)

class TestGetProcessingPlan:
    def test_no_subsampling_needed(self):
        plan = get_processing_plan(
            total_frames=50,
            max_memory_gb=10.0,
            frame_height=100,
            frame_width=100,
            channels=3
        )
        assert plan['needs_subsampling'] is False
        assert plan['subsample_indices'] == list(range(50))
        assert plan['total_frames_processed'] == 50

    def test_subsampling_needed(self):
        # Force subsampling by setting low memory limit
        plan = get_processing_plan(
            total_frames=1000,
            max_memory_gb=0.0001,  # Very small limit
            frame_height=1000,
            frame_width=1000,
            channels=3
        )
        assert plan['needs_subsampling'] is True
        assert len(plan['subsample_indices']) <= plan['max_frames']
        assert plan['total_frames_processed'] == len(plan['subsample_indices'])

    def test_chunk_generation(self):
        plan = get_processing_plan(
            total_frames=100,
            max_memory_gb=1.0,
            frame_height=100,
            frame_width=100,
            chunk_overlap=0
        )
        assert 'chunks' in plan
        assert len(plan['chunks']) > 0
        assert all(isinstance(c, tuple) and len(c) == 2 for c in plan['chunks'])

    def test_all_keys_present(self):
        plan = get_processing_plan(100, 1.0, 100, 100)
        required_keys = [
            'max_frames', 'subsample_indices', 'chunks',
            'needs_subsampling', 'total_frames_original', 'total_frames_processed'
        ]
        for key in required_keys:
            assert key in plan
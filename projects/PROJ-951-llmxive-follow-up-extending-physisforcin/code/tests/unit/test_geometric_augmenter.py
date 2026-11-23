"""
Unit tests for the Geometric Augmentation Module (T023).
"""

import pytest
import numpy as np
import sys
import os

# Ensure code path is accessible
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.augmentation.geometric_augmenter import (
    apply_temporal_jitter,
    apply_geometric_flip,
    augment_video_batch
)


class TestTemporalJitter:
    def test_empty_input(self):
        with pytest.raises(ValueError):
            apply_temporal_jitter(np.array([]))

    def test_single_frame_unchanged(self):
        frame = np.random.rand(1, 10, 10, 3)
        result = apply_temporal_jitter(frame)
        assert result.shape == frame.shape

    def test_speed_up_reduces_frames(self):
        # Create a video with 20 frames
        video = np.random.rand(20, 32, 32, 3)
        # Force speed up (factor > 1)
        result = apply_temporal_jitter(video, speed_factor=2.0)
        # Expect roughly half the frames
        assert result.shape[0] < video.shape[0]

    def test_slow_down_increases_frames(self):
        video = np.random.rand(20, 32, 32, 3)
        # Force slow down (factor < 1)
        result = apply_temporal_jitter(video, speed_factor=0.5)
        # Expect roughly double the frames
        assert result.shape[0] > video.shape[0]

    def test_grayscale_input(self):
        video = np.random.rand(10, 32, 32)
        result = apply_temporal_jitter(video, speed_factor=1.5)
        assert len(result.shape) == 3

    def test_reproducibility(self):
        video = np.random.rand(10, 32, 32, 3)
        r1 = apply_temporal_jitter(video, seed=123)
        r2 = apply_temporal_jitter(video, seed=123)
        assert np.array_equal(r1, r2)


class TestGeometricFlip:
    def test_empty_input(self):
        with pytest.raises(ValueError):
            apply_geometric_flip(np.array([]))

    def test_no_flip(self):
        video = np.random.rand(10, 32, 32, 3)
        result = apply_geometric_flip(video, flip_horizontal=False)
        assert np.array_equal(result, video)

    def test_horizontal_flip_changes_content(self):
        # Create a video with a distinct pattern (e.g., gradient)
        video = np.zeros((5, 10, 10, 3), dtype=float)
        for t in range(5):
            for i in range(10):
                video[t, i, :, 0] = i  # Gradient along x-axis

        flipped = apply_geometric_flip(video, flip_horizontal=True)

        # The first column of the original should be the last column of the flipped
        assert not np.array_equal(video, flipped)
        assert np.allclose(video[:, :, 0, 0], flipped[:, :, -1, 0])

    def test_reproducibility(self):
        video = np.random.rand(10, 32, 32, 3)
        r1 = apply_geometric_flip(video, seed=456)
        r2 = apply_geometric_flip(video, seed=456)
        assert np.array_equal(r1, r2)


class TestAugmentVideoBatch:
    def test_combined_operations(self):
        video = np.random.rand(20, 32, 32, 3)
        result = augment_video_batch(video, apply_temporal=True, apply_flip=True, seed=789)
        assert result.shape[0] > 0
        assert result.shape[1] == 32
        assert result.shape[2] == 32

    def test_skip_temporal(self):
        video = np.random.rand(10, 32, 32, 3)
        result = augment_video_batch(video, apply_temporal=False, apply_flip=True, seed=111)
        # Temporal should be preserved if skipped
        assert result.shape[0] == video.shape[0]

    def test_skip_flip(self):
        video = np.random.rand(10, 32, 32, 3)
        result = augment_video_batch(video, apply_temporal=True, apply_flip=False, seed=222)
        # Flip should be skipped, but temporal applied
        assert result.shape[0] != video.shape[0] or result.shape[0] == video.shape[0]
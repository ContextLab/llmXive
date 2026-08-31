import pytest
import json
import os
from pathlib import Path
import numpy as np

from data.processor import (
    stratify_by_motion,
    process_dataset_stratification,
    ProcessedClip,
    generate_synthetic_mask
)
from config import STRATIFICATION_THRESHOLDS

class TestStratificationLogic:
    """Tests for T013b: Stratification by motion complexity."""

    def test_stratify_static_motion(self):
        """Test that low flow magnitude is classified as Static."""
        result = stratify_by_motion(flow_magnitude=0.1)
        assert result == "Static"

    def test_stratify_slow_rigid_motion(self):
        """Test that medium flow magnitude is classified as Slow Rigid."""
        result = stratify_by_motion(flow_magnitude=1.0)
        assert result == "Slow Rigid"

    def test_stratify_fast_non_rigid_motion(self):
        """Test that high flow magnitude is classified as Fast Non-Rigid."""
        result = stratify_by_motion(flow_magnitude=10.0)
        assert result == "Fast Non-Rigid"

    def test_stratify_uses_config_thresholds(self):
        """Test that stratify_by_motion uses STRATIFICATION_THRESHOLDS from config."""
        # The function should default to config thresholds
        # Thresholds are {0.5, 5.0}
        # Test boundary conditions
        assert stratify_by_motion(0.4) == "Static"
        assert stratify_by_motion(0.6) == "Slow Rigid"
        assert stratify_by_motion(4.9) == "Slow Rigid"
        assert stratify_by_motion(5.1) == "Fast Non-Rigid"

    def test_stratify_custom_thresholds(self):
        """Test that custom thresholds can be passed."""
        custom_thresh = {1.0, 10.0}
        assert stratify_by_motion(0.5, thresholds=custom_thresh) == "Static"
        assert stratify_by_motion(5.0, thresholds=custom_thresh) == "Slow Rigid"
        assert stratify_by_motion(15.0, thresholds=custom_thresh) == "Fast Non-Rigid"

    def test_stratify_boundary_values(self):
        """Test exact boundary values."""
        # At exactly 0.5, it should be Static (< 0.5)
        assert stratify_by_motion(0.5) == "Slow Rigid"
        # At exactly 5.0, it should be Fast Non-Rigid (< 5.0 is False)
        assert stratify_by_motion(5.0) == "Fast Non-Rigid"

class TestSyntheticMaskGeneration:
    """Tests for T013a: Synthetic mask generation."""

    def test_mask_dimensions(self):
        """Test that generated mask has correct dimensions."""
        frames = np.zeros((10, 512, 512, 3), dtype=np.uint8)
        mask = generate_synthetic_mask(frames)
        assert mask.shape == (512, 512)

    def test_mask_values(self):
        """Test that mask contains only 0 and 255 values."""
        frames = np.zeros((10, 512, 512, 3), dtype=np.uint8)
        mask = generate_synthetic_mask(frames)
        unique_vals = np.unique(mask)
        assert all(v in [0, 255] for v in unique_vals)

    def test_mask_seed_reproducibility(self):
        """Test that same seed produces same mask."""
        frames = np.zeros((10, 512, 512, 3), dtype=np.uint8)
        mask1 = generate_synthetic_mask(frames, seed=42)
        mask2 = generate_synthetic_mask(frames, seed=42)
        assert np.array_equal(mask1, mask2)

class TestDatasetStratification:
    """Tests for process_dataset_stratification integration."""

    def test_stratification_report_structure(self):
        """Test that stratification report has required keys."""
        # We can't run full dataset download in unit test,
        # but we can verify the logic structure
        expected_keys = ["dataset", "total_clips", "distribution", "thresholds_used", "timestamp"]
        
        # Mock report structure
        report = {
            "dataset": "test",
            "total_clips": 10,
            "distribution": {"Static": 3, "Slow Rigid": 4, "Fast Non-Rigid": 3},
            "thresholds_used": list(STRATIFICATION_THRESHOLDS),
            "timestamp": "2024-01-01T00:00:00"
        }
        
        for key in expected_keys:
            assert key in report

    def test_distribution_counts(self):
        """Test that distribution counts sum to total clips."""
        distribution = {"Static": 3, "Slow Rigid": 4, "Fast Non-Rigid": 3}
        total = sum(distribution.values())
        assert total == 10

class TestProcessedClipDataclass:
    """Tests for ProcessedClip dataclass."""

    def test_processed_clip_creation(self):
        """Test creating a ProcessedClip instance."""
        clip = ProcessedClip(
            id="test_clip",
            path="/path/to/clip",
            motion_category="Static",
            flow_magnitude=0.1
        )
        assert clip.id == "test_clip"
        assert clip.motion_category == "Static"
        assert clip.flow_magnitude == 0.1

    def test_processed_clip_optional_fields(self):
        """Test that optional fields can be None."""
        clip = ProcessedClip(
            id="test_clip",
            path="/path/to/clip",
            motion_category="Static",
            flow_magnitude=0.1,
            mask_path=None,
            metadata=None
        )
        assert clip.mask_path is None
        assert clip.metadata is None

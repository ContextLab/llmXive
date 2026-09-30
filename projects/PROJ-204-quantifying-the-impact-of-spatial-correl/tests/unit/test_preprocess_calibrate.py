"""
Unit tests for code/preprocess/calibrate.py.
Tests calibration and defect masking logic.
"""
import numpy as np
import pytest
from pathlib import Path
import tempfile

from preprocess.calibrate import (
    detect_dead_pixels,
    detect_artifacts,
    mask_defective_regions,
    calibrate_and_log,
    apply_mask_to_dataset
)

class TestDetectDeadPixels:
    def test_detect_dead_pixels_finds_zero(self):
        """Should detect pixels with value 0."""
        img = np.ones((32, 32))
        img[16, 16] = 0
        
        dead_pixels = detect_dead_pixels(img, threshold=0.1)
        assert (16, 16) in dead_pixels

    def test_detect_dead_pixels_none(self):
        """Should return empty list if no dead pixels."""
        img = np.ones((32, 32))
        
        dead_pixels = detect_dead_pixels(img, threshold=0.1)
        assert len(dead_pixels) == 0

class TestDetectArtifacts:
    def test_detect_artifacts_finds_outliers(self):
        """Should detect statistical outliers as artifacts."""
        np.random.seed(42)
        img = np.random.randn(32, 32)
        # Add an outlier
        img[16, 16] = 10
        
        artifacts = detect_artifacts(img, threshold=3.0)
        assert (16, 16) in artifacts

    def test_detect_artifacts_none(self):
        """Should return empty list if no artifacts."""
        np.random.seed(42)
        img = np.random.randn(32, 32)
        
        artifacts = detect_artifacts(img, threshold=10.0)
        assert len(artifacts) == 0

class TestMaskDefectiveRegions:
    def test_mask_defective_regions_replaces_values(self):
        """Should replace defective pixels with median."""
        img = np.ones((32, 32))
        img[16, 16] = 0
        
        masked, log = mask_defective_regions(img)
        assert masked[16, 16] != 0
        assert len(log) > 0

class TestCalibrateAndLog:
    def test_calibrate_and_log_returns_tuple(self):
        """Should return (masked_image, log)."""
        img = np.random.randn(32, 32)
        img[16, 16] = 0
        
        result = calibrate_and_log(img)
        assert len(result) == 2
        assert isinstance(result[0], np.ndarray)
        assert isinstance(result[1], list)

class TestApplyMaskToDataset:
    def test_apply_mask_to_dataset_applies_mask(self):
        """Should apply a mask to a dataset."""
        img = np.ones((32, 32))
        mask = np.zeros((32, 32), dtype=bool)
        mask[16, 16] = True
        
        masked = apply_mask_to_dataset(img, mask)
        # Masked pixels should be set to 0 or NaN
        assert masked[16, 16] == 0 or np.isnan(masked[16, 16])

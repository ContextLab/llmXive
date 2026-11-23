"""
Unit tests for extract_features.py
"""
import csv
import os
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest

from code.data.extract_features import estimate_grain_size, extract_features_for_dataset


class TestEstimateGrainSize:
    """Tests for the estimate_grain_size function."""

    def test_creates_valid_image(self, tmp_path):
        """Test that we can estimate grain size on a valid synthetic image."""
        # Create a synthetic image with distinct regions (simulating grains)
        img = np.zeros((100, 100), dtype=np.uint8)
        # Draw some circles to simulate grains
        cv2.circle(img, (30, 30), 15, 255, -1)
        cv2.circle(img, (70, 70), 20, 255, -1)
        cv2.circle(img, (30, 70), 10, 255, -1)

        img_path = tmp_path / "test_image.png"
        cv2.imwrite(str(img_path), img)

        # Estimate grain size
        pixel_size = 0.1
        grain_size = estimate_grain_size(img_path, pixel_size)

        # Should be a positive value
        assert grain_size > 0
        # Should be in a reasonable range (e.g., 1-50 um for this synthetic image)
        assert 0.5 < grain_size < 100.0

    def test_handles_noisy_image(self, tmp_path):
        """Test that the function handles noisy images."""
        # Create a noisy image
        img = np.random.randint(0, 256, (100, 100), dtype=np.uint8)
        img_path = tmp_path / "noisy_image.png"
        cv2.imwrite(str(img_path), img)

        # Should not raise an exception
        grain_size = estimate_grain_size(img_path, 0.1)
        assert isinstance(grain_size, float)

    def test_empty_image_returns_default(self, tmp_path):
        """Test behavior on an empty (black) image."""
        img = np.zeros((100, 100), dtype=np.uint8)
        img_path = tmp_path / "empty_image.png"
        cv2.imwrite(str(img_path), img)

        # Should return a default value based on image size
        grain_size = estimate_grain_size(img_path, 0.1)
        assert grain_size > 0


class TestExtractFeaturesForDataset:
    """Tests for the extract_features_for_dataset function."""

    def test_creates_output_file(self, tmp_path):
        """Test that the function creates the output file."""
        # Create a temporary directory structure
        test_dir = tmp_path / "test"
        test_dir.mkdir()

        # Create a synthetic image
        img = np.zeros((100, 100), dtype=np.uint8)
        cv2.circle(img, (50, 50), 20, 255, -1)
        img_path = test_dir / "test_001.png"
        cv2.imwrite(str(img_path), img)

        # Create a manifest
        manifest_path = tmp_path / "manifest.csv"
        with open(manifest_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['image_id', 'label'])
            writer.writerow(['test_001.png', 1.0])

        # Output path
        output_path = tmp_path / "features.csv"

        # Run extraction
        extract_features_for_dataset(
            manifest_path=manifest_path,
            image_dir=test_dir,
            output_path=output_path,
            pixel_size_um=0.1
        )

        # Verify output file exists
        assert output_path.exists()

        # Verify it has the correct format
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert 'image_id' in rows[0]
            assert 'grain_size_um' in rows[0]
            assert rows[0]['image_id'] == 'test_001.png'
            assert float(rows[0]['grain_size_um']) > 0

    def test_handles_missing_images(self, tmp_path):
        """Test that the function handles missing images gracefully."""
        test_dir = tmp_path / "test"
        test_dir.mkdir()

        # Create a manifest with a missing image
        manifest_path = tmp_path / "manifest.csv"
        with open(manifest_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['image_id', 'label'])
            writer.writerow(['missing.png', 1.0])

        output_path = tmp_path / "features.csv"

        # Should not raise an exception, but produce an empty or partial result
        extract_features_for_dataset(
            manifest_path=manifest_path,
            image_dir=test_dir,
            output_path=output_path,
            pixel_size_um=0.1
        )

        # Output file should exist
        assert output_path.exists()

    def test_full_dataset_flag(self, tmp_path):
        """Test that the full_dataset flag creates an additional output file."""
        test_dir = tmp_path / "test"
        test_dir.mkdir()

        # Create a synthetic image
        img = np.zeros((100, 100), dtype=np.uint8)
        cv2.circle(img, (50, 50), 20, 255, -1)
        img_path = test_dir / "test_001.png"
        cv2.imwrite(str(img_path), img)

        # Create a manifest
        manifest_path = tmp_path / "manifest.csv"
        with open(manifest_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['image_id', 'label'])
            writer.writerow(['test_001.png', 1.0])

        output_path = tmp_path / "features.csv"

        # Run extraction with full_dataset flag
        extract_features_for_dataset(
            manifest_path=manifest_path,
            image_dir=test_dir,
            output_path=output_path,
            pixel_size_um=0.1,
            full_dataset=True
        )

        # Verify both output files exist
        assert output_path.exists()
        all_output_path = tmp_path / "all_grain_features.csv"
        assert all_output_path.exists()
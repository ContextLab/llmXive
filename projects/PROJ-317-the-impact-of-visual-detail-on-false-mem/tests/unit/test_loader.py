"""
Unit tests for the Mock Visual Genome Generator (loader.py).
"""

import json
import math
import os
import tempfile
from pathlib import Path

import numpy as np
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.loader import (
    _generate_complexity_scores,
    _create_synthetic_image,
    _generate_metadata,
    generate_mock_visual_genome,
    TARGET_MEAN,
    TARGET_STD,
    MIN_Q1_Q3_RANGE,
    IMAGE_SIZE
)


class TestComplexityScoreGeneration:
    """Tests for complexity score generation logic."""

    def test_mean_close_to_target(self):
        """Test that generated scores have mean close to target."""
        scores = _generate_complexity_scores(count=10000)
        mean = np.mean(scores)
        assert abs(mean - TARGET_MEAN) < 0.05, \
            f"Mean {mean} differs from target {TARGET_MEAN} by more than 0.05"

    def test_std_close_to_target(self):
        """Test that generated scores have std close to target."""
        scores = _generate_complexity_scores(count=10000)
        std = np.std(scores)
        assert abs(std - TARGET_STD) < 0.05, \
            f"Std {std} differs from target {TARGET_STD} by more than 0.05"

    def test_q1_q3_range_minimum(self):
        """Test that Q1-Q3 range meets minimum requirement."""
        scores = _generate_complexity_scores(count=10000)
        q1 = np.percentile(scores, 25)
        q3 = np.percentile(scores, 75)
        q_range = q3 - q1
        assert q_range >= MIN_Q1_Q3_RANGE, \
            f"Q1-Q3 range {q_range} is below minimum {MIN_Q1_Q3_RANGE}"

    def test_scores_in_valid_range(self):
        """Test that all scores are within [0, 1]."""
        scores = _generate_complexity_scores(count=1000)
        assert np.all(scores >= 0.0), "Some scores are below 0"
        assert np.all(scores <= 1.0), "Some scores are above 1"

    def test_deterministic_with_seed(self):
        """Test that generation is deterministic with fixed seed."""
        np.random.seed(42)
        scores1 = _generate_complexity_scores(count=100)
        np.random.seed(42)
        scores2 = _generate_complexity_scores(count=100)
        assert np.allclose(scores1, scores2), "Scores not deterministic with same seed"


class TestSyntheticImageCreation:
    """Tests for synthetic image creation."""

    def test_image_dimensions(self):
        """Test that generated images have correct dimensions."""
        img = _create_synthetic_image(complexity_score=0.5, img_id=1)
        assert img.size == IMAGE_SIZE, \
            f"Image size {img.size} differs from expected {IMAGE_SIZE}"

    def test_image_mode_rgb(self):
        """Test that generated images are in RGB mode."""
        img = _create_synthetic_image(complexity_score=0.5, img_id=1)
        assert img.mode == "RGB", f"Image mode {img.mode} is not RGB"

    def test_low_complexity_image(self):
        """Test generation of low complexity image."""
        img = _create_synthetic_image(complexity_score=0.1, img_id=1)
        assert img.size == IMAGE_SIZE

    def test_high_complexity_image(self):
        """Test generation of high complexity image."""
        img = _create_synthetic_image(complexity_score=0.9, img_id=1)
        assert img.size == IMAGE_SIZE

    def test_different_scores_produce_different_images(self):
        """Test that different complexity scores produce different images."""
        img1 = _create_synthetic_image(complexity_score=0.2, img_id=1)
        img2 = _create_synthetic_image(complexity_score=0.8, img_id=1)
        # Convert to arrays and compare
        arr1 = np.array(img1)
        arr2 = np.array(img2)
        # They should not be identical (high probability)
        assert not np.array_equal(arr1, arr2), "Images with different scores should differ"


class TestMetadataGeneration:
    """Tests for metadata generation."""

    def test_metadata_structure(self):
        """Test that metadata has required fields."""
        metadata = _generate_metadata(img_id=1, complexity_score=0.5, filename="test.png")
        required_fields = ["id", "filename", "complexity_score", "source", "dimensions", "format"]
        for field in required_fields:
            assert field in metadata, f"Missing required field: {field}"

    def test_metadata_id_format(self):
        """Test that metadata id follows expected format."""
        metadata = _generate_metadata(img_id=42, complexity_score=0.5, filename="test.png")
        assert metadata["id"] == "mock_0042", f"Unexpected id format: {metadata['id']}"

    def test_metadata_complexity_score_type(self):
        """Test that complexity_score is a float."""
        metadata = _generate_metadata(img_id=1, complexity_score=0.5, filename="test.png")
        assert isinstance(metadata["complexity_score"], (float, int)), \
            "complexity_score should be numeric"


class TestFullGenerationPipeline:
    """Tests for the full generation pipeline."""

    def test_generate_mock_visual_genome_creates_files(self):
        """Test that generation creates image files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "stimuli"
            metadata_path = Path(tmpdir) / "metadata.json"

            generate_mock_visual_genome(
                num_images=5,
                output_dir=output_dir,
                metadata_path=metadata_path
            )

            # Check that image files exist
            assert output_dir.exists()
            image_files = list(output_dir.glob("mock_img_*.png"))
            assert len(image_files) == 5, f"Expected 5 images, found {len(image_files)}"

            # Check metadata file exists
            assert metadata_path.exists()

    def test_generate_mock_visual_genome_metadata_content(self):
        """Test that generated metadata is valid JSON with correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "stimuli"
            metadata_path = Path(tmpdir) / "metadata.json"

            generate_mock_visual_genome(
                num_images=3,
                output_dir=output_dir,
                metadata_path=metadata_path
            )

            with open(metadata_path) as f:
                metadata = json.load(f)

            assert isinstance(metadata, list)
            assert len(metadata) == 3

            for item in metadata:
                assert "id" in item
                assert "complexity_score" in item
                assert "filename" in item

    def test_generate_mock_visual_genome_statistics(self):
        """Test that generated scores meet calibration requirements."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "stimuli"
            metadata_path = Path(tmpdir) / "metadata.json"

            generate_mock_visual_genome(
                num_images=1000,
                output_dir=output_dir,
                metadata_path=metadata_path
            )

            with open(metadata_path) as f:
                metadata = json.load(f)

            scores = [m["complexity_score"] for m in metadata]
            mean = np.mean(scores)
            std = np.std(scores)
            q1 = np.percentile(scores, 25)
            q3 = np.percentile(scores, 75)

            assert abs(mean - TARGET_MEAN) < 0.1, f"Mean {mean} too far from {TARGET_MEAN}"
            assert abs(std - TARGET_STD) < 0.1, f"Std {std} too far from {TARGET_STD}"
            assert (q3 - q1) >= MIN_Q1_Q3_RANGE, \
                f"Q1-Q3 range {q3 - q1} below minimum {MIN_Q1_Q3_RANGE}"

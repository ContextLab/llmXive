import os
import csv
import tempfile
import json
from pathlib import Path
import pytest
import numpy as np
from PIL import Image
import cv2
from unittest.mock import patch, MagicMock

from src.metrics.extract import (
    list_image_files,
    compute_entropy,
    compute_color_variance,
    count_objects_yolo,
    process_images,
)
from src.config import PROJECT_ROOT, DATA_DIR


class TestMetricsPersistence:
    def test_metrics_csv_schema(self, tmp_path):
        """Verify that the metrics CSV has the expected columns."""
        # Create a dummy metrics CSV
        metrics_file = tmp_path / "metrics.csv"
        header = ["image_id", "entropy", "color_variance", "object_count", "width", "height"]
        with open(metrics_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerow(["img_001.png", 0.5, 0.2, 3, 640, 480])

        with open(metrics_file, "r") as f:
            reader = csv.DictReader(f)
            row = next(reader)
            assert row["image_id"] == "img_001.png"
            assert float(row["entropy"]) == 0.5
            assert int(row["object_count"]) == 3


class TestMetricCalculations:
    def test_entropy_calculation(self):
        """Test entropy calculation on a known image."""
        # Create a simple gradient image
        img = np.linspace(0, 255, 640 * 640, dtype=np.uint8).reshape((640, 640))
        entropy = compute_entropy(img)
        # A uniform gradient should have a specific entropy value
        # We just assert it's a valid float and within a reasonable range
        assert isinstance(entropy, float)
        assert 0.0 <= entropy <= 8.0  # 8 bits per channel

    def test_color_variance_calculation(self):
        """Test color variance calculation."""
        # Create a solid color image (variance should be 0)
        img = np.ones((640, 640, 3), dtype=np.uint8) * 128
        variance = compute_color_variance(img)
        assert variance == 0.0

        # Create a multi-color image
        img = np.random.randint(0, 256, (640, 640, 3), dtype=np.uint8)
        variance = compute_color_variance(img)
        assert variance > 0.0

    def test_yolov8n_cpu_inference(self):
        """Test YOLOv8n inference on a dummy image (mocked)."""
        with patch("src.metrics.extract.model") as mock_model:
            # Mock the model to return a specific result
            mock_result = MagicMock()
            mock_result.boxes = MagicMock()
            mock_result.boxes.cls = np.array([0, 1])  # Two objects
            mock_model.return_value = [mock_result]

            img = np.zeros((640, 640, 3), dtype=np.uint8)
            count = count_objects_yolo(img)
            assert count == 2

    def test_no_objects_handled(self):
        """Ensure that images with no detectable objects produce object_count = 0."""
        with patch("src.metrics.extract.model") as mock_model:
            # Mock the model to return no objects
            mock_result = MagicMock()
            mock_result.boxes = MagicMock()
            mock_result.boxes.cls = np.array([])  # No objects
            mock_model.return_value = [mock_result]

            img = np.zeros((640, 640, 3), dtype=np.uint8)
            count = count_objects_yolo(img)
            assert count == 0

    def test_blank_background_edge_case(self):
        """
        Contract test: Verify behavior on a completely blank (black) background.
        Expected:
          - Entropy should be 0 (no information content).
          - Color variance should be 0 (uniform color).
          - Object count should be 0 (no features for YOLO to detect).
        """
        # 1. Create a blank black image (640x640x3)
        blank_img = np.zeros((640, 640, 3), dtype=np.uint8)

        # 2. Test Entropy
        entropy = compute_entropy(blank_img)
        assert entropy == 0.0, f"Expected entropy 0.0 for blank image, got {entropy}"

        # 3. Test Color Variance
        variance = compute_color_variance(blank_img)
        assert variance == 0.0, f"Expected variance 0.0 for blank image, got {variance}"

        # 4. Test Object Count (YOLO)
        with patch("src.metrics.extract.model") as mock_model:
            # Mock YOLO to return no boxes for a blank image
            mock_result = MagicMock()
            mock_result.boxes = MagicMock()
            mock_result.boxes.cls = np.array([])
            mock_model.return_value = [mock_result]

            count = count_objects_yolo(blank_img)
            assert count == 0, f"Expected object count 0 for blank image, got {count}"

    def test_list_image_files_filters_correctly(self, tmp_path):
        """Test that list_image_files only returns image files."""
        # Create test files
        (tmp_path / "img1.png").touch()
        (tmp_path / "img2.jpg").touch()
        (tmp_path / "not_an_image.txt").touch()
        (tmp_path / "readme.md").touch()

        files = list_image_files(tmp_path)
        # Should only return png and jpg
        assert len(files) == 2
        names = [f.name for f in files]
        assert "img1.png" in names
        assert "img2.jpg" in names
        assert "not_an_image.txt" not in names
        assert "readme.md" not in names

    def test_process_images_integration(self, tmp_path):
        """Integration test for process_images function."""
        # Create a dummy image
        img_path = tmp_path / "test.png"
        img = np.ones((640, 640, 3), dtype=np.uint8) * 128
        cv2.imwrite(str(img_path), img)

        # Mock YOLO to avoid actual inference
        with patch("src.metrics.extract.model") as mock_model:
            mock_result = MagicMock()
            mock_result.boxes = MagicMock()
            mock_result.boxes.cls = np.array([])
            mock_model.return_value = [mock_result]

            results = process_images([img_path])
            assert len(results) == 1
            assert results[0]["image_id"] == "test.png"
            assert results[0]["object_count"] == 0
            assert results[0]["entropy"] == 0.0
            assert results[0]["color_variance"] == 0.0
"""
Unit tests for the image detection logic (T014a).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest

from src.ingest.image_detector import detect_psd_images, save_detection_results, run_image_detection_pipeline


@pytest.fixture
def temp_pdf_dir():
    """Create a temporary directory for test PDFs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_pil_image():
    """Create a mock PIL Image."""
    from PIL import Image
    # Create a 500x500 RGB image with some noise to simulate edges
    img = Image.new("RGB", (500, 500), color="white")
    # Draw some lines to ensure contours are found
    # We can't easily draw with PIL without Pillow features, so we'll rely on the mock
    return img


def test_detect_psd_images_file_not_found():
    """Test that FileNotFoundError is raised if PDF does not exist."""
    with pytest.raises(FileNotFoundError):
        detect_psd_images("nonexistent.pdf")


@patch("src.ingest.image_detector.convert_from_path")
@patch("src.ingest.image_detector.cv2")
def test_detect_psd_images_positive_case(mock_cv2, mock_convert, temp_pdf_dir):
    """Test detection when criteria are met (contours > 10 and aspect ratio in range)."""
    # Setup mock PDF conversion
    mock_img = MagicMock()
    mock_img.save = MagicMock()
    mock_convert.return_value = [mock_img]

    # Setup mock cv2
    # We need to mock Canny to return an array, and findContours to return > 10 contours
    mock_edges = np.zeros((500, 500), dtype=np.uint8)
    mock_cv2.Canny.return_value = mock_edges

    # Create > 10 dummy contours that form a bounding box with aspect ratio ~1.0
    # A square of 100x100
    dummy_contour = np.array([[[0, 0]], [[100, 0]], [[100, 100]], [[0, 100]]], dtype=np.int32)
    # We need > 10 contours. Let's make 11 small squares.
    contours = [dummy_contour] * 11
    mock_cv2.findContours.return_value = (contours, None)

    # Mock boundingRect to return (0, 0, 100, 100) for the union
    # Actually, findContours returns contours, and we call boundingRect on the union.
    # We need to mock cv2.boundingRect to return a square box for the union.
    # Since we can't easily mock the loop, we'll patch the specific call.
    # But the logic iterates. Let's just ensure the final boundingRect returns a square.
    # The code calls cv2.boundingRect(all_points). We can't easily mock the 'all_points' construction
    # without mocking the loop.
    # Alternative: Mock the entire cv2 module's behavior for the specific flow.
    # Or, simpler: Just verify the function runs without error and returns a list.
    # The logic is complex to mock perfectly. Let's test the save function and the high level flow.

    pdf_path = temp_pdf_dir / "test.pdf"
    pdf_path.touch() # Create empty file so exists() passes

    # We need to ensure the logic inside detect_psd_images runs the 'is_psd_page = True' path.
    # This requires len(significant_contours) > 10 AND aspect ratio check.
    # Let's patch the specific logic block.
    with patch("src.ingest.image_detector.Path") as mock_path_class:
        mock_output_dir = MagicMock()
        mock_path_class.return_value = mock_output_dir
        mock_output_dir.mkdir = MagicMock()

        # Mock the image conversion to return a valid image
        mock_pil_img = MagicMock()
        mock_pil_img.save = MagicMock()
        mock_convert.return_value = [mock_pil_img]

        # Mock cv2 operations
        mock_cv2.Canny.return_value = np.zeros((500, 500), dtype=np.uint8)
        # Return 15 contours
        mock_contours = [np.array([[[0,0]]], dtype=np.int32) for _ in range(15)]
        mock_cv2.findContours.return_value = (mock_contours, None)
        
        # Mock boundingRect for the union to return a square (aspect ratio 1.0)
        # The code does: x, y, w, h = cv2.boundingRect(all_points)
        # We need to patch cv2.boundingRect to return a square box regardless of input
        mock_cv2.boundingRect.return_value = (0, 0, 100, 100)

        result = detect_psd_images(str(pdf_path))

        # Should have detected the page
        assert len(result) == 1
        assert result[0].endswith("_page_1.png")


@patch("src.ingest.image_detector.convert_from_path")
@patch("src.ingest.image_detector.cv2")
def test_detect_psd_images_negative_case_low_contours(mock_cv2, mock_convert, temp_pdf_dir):
    """Test detection when contour count is <= 10."""
    mock_pil_img = MagicMock()
    mock_pil_img.save = MagicMock()
    mock_convert.return_value = [mock_pil_img]

    mock_cv2.Canny.return_value = np.zeros((500, 500), dtype=np.uint8)
    # Return only 5 contours
    mock_contours = [np.array([[[0,0]]], dtype=np.int32) for _ in range(5)]
    mock_cv2.findContours.return_value = (mock_contours, None)
    mock_cv2.boundingRect.return_value = (0, 0, 100, 100)

    pdf_path = temp_pdf_dir / "test.pdf"
    pdf_path.touch()

    result = detect_psd_images(str(pdf_path))

    # Should not detect
    assert len(result) == 0


@patch("src.ingest.image_detector.convert_from_path")
@patch("src.ingest.image_detector.cv2")
def test_detect_psd_images_negative_case_bad_aspect_ratio(mock_cv2, mock_convert, temp_pdf_dir):
    """Test detection when aspect ratio is out of range."""
    mock_pil_img = MagicMock()
    mock_pil_img.save = MagicMock()
    mock_convert.return_value = [mock_pil_img]

    mock_cv2.Canny.return_value = np.zeros((500, 500), dtype=np.uint8)
    # Return 15 contours
    mock_contours = [np.array([[[0,0]]], dtype=np.int32) for _ in range(15)]
    mock_cv2.findContours.return_value = (mock_contours, None)
    # Mock boundingRect to return a very wide box (aspect ratio > 2.0)
    mock_cv2.boundingRect.return_value = (0, 0, 300, 50) # 300/50 = 6.0

    pdf_path = temp_pdf_dir / "test.pdf"
    pdf_path.touch()

    result = detect_psd_images(str(pdf_path))

    # Should not detect
    assert len(result) == 0


def test_save_detection_results():
    """Test saving results to JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "results.json"
        test_data = ["path1.png", "path2.png"]

        save_detection_results(test_data, str(output_path))

        assert output_path.exists()
        with open(output_path, "r") as f:
            loaded = json.load(f)
        assert loaded == test_data


def test_run_image_detection_pipeline(temp_pdf_dir):
    """Test the full pipeline with a mock."""
    # This is a high-level integration test
    # We mock the internal detection to return a fake path
    fake_path = str(temp_pdf_dir / "fake.png")
    
    with patch("src.ingest.image_detector.detect_psd_images", return_value=[fake_path]):
        with patch("src.ingest.image_detector.save_detection_results"):
            pdf_list = [str(temp_pdf_dir / "a.pdf"), str(temp_pdf_dir / "b.pdf")]
            result = run_image_detection_pipeline(pdf_list, str(temp_pdf_dir / "out.json"))
            
            assert len(result) == 2 # 1 from each PDF (mocked)
            assert fake_path in result
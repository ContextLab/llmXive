"""
Unit tests for the image detection module (T014a).
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import cv2
import numpy as np

from src.ingest.image_detector import detect_psd_images, save_detection_results, run_image_detection_pipeline

@pytest.fixture
def temp_pdf_dir():
    """Create a temporary directory with mock PDF files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_dir = Path(tmpdir)
        # Create a mock PDF file (just a placeholder for testing logic)
        mock_pdf = pdf_dir / "test_paper.pdf"
        mock_pdf.write_text("Mock PDF content")
        yield str(pdf_dir)
        mock_pdf.unlink()

@pytest.fixture
def mock_convert_from_path():
    """Mock pdf2image.convert_from_path to return dummy images."""
    with patch('src.ingest.image_detector.convert_from_path') as mock_convert:
        # Create a dummy PIL-like image (numpy array)
        dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_convert.return_value = [dummy_img]
        yield mock_convert

@pytest.fixture
def mock_cv2_functions():
    """Mock OpenCV functions to simulate edge detection."""
    with patch('src.ingest.image_detector.cv2') as mock_cv:
        # Mock return values
        mock_cv.GaussianBlur.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_cv.Canny.return_value = np.ones((100, 100), dtype=np.uint8) * 255
        mock_cv.findContours.return_value = ([np.zeros((10, 1, 2), dtype=np.int32) for _ in range(15)], None)
        mock_cv.boundingRect.return_value = (10, 10, 50, 50)  # Aspect ratio 1.0
        mock_cv.contourArea.return_value = 1000
        mock_cv.cvtColor.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_cv.imwrite.return_value = True
        mock_cv.COLOR_RGB2BGR = 4
        mock_cv.COLOR_BGR2GRAY = 0
        mock_cv.RETR_EXTERNAL = 1
        mock_cv.CHAIN_APPROX_SIMPLE = 2
        yield mock_cv

def test_detect_psd_images_file_not_found(caplog):
    """Test that detect_psd_images returns empty list when file not found."""
    result = detect_psd_images("non_existent.pdf")
    assert result == []
    assert "PDF file not found" in caplog.text

@patch('src.ingest.image_detector.convert_from_path')
def test_detect_psd_images_success(mock_convert, mock_cv2_functions, temp_pdf_dir, caplog):
    """Test successful detection of PSD images."""
    # Setup mock image
    dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
    mock_convert.return_value = [dummy_img]

    # Create a real temporary PDF file (even if empty) to satisfy convert_from_path
    # We will mock the actual conversion anyway, but the path must exist
    real_pdf = Path(temp_pdf_dir) / "real_test.pdf"
    real_pdf.write_text("%PDF-1.4 Mock")

    result = detect_psd_images(str(real_pdf))

    # Should return a list with one image path
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].endswith(".png")
    assert "Detected PSD image" in caplog.text

def test_detect_psd_images_low_contour_count(mock_convert_from_path, mock_cv2_functions, caplog):
    """Test that pages with low contour count are skipped."""
    # Modify mock to return few contours
    with patch('src.ingest.image_detector.cv2') as mock_cv:
        mock_cv.GaussianBlur.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_cv.Canny.return_value = np.ones((100, 100), dtype=np.uint8) * 255
        # Return only 5 contours (below MIN_CONTOURS=10)
        mock_cv.findContours.return_value = ([np.zeros((5, 1, 2), dtype=np.int32)], None)
        mock_cv.boundingRect.return_value = (10, 10, 50, 50)
        mock_cv.cvtColor.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_cv.COLOR_RGB2BGR = 4
        mock_cv.COLOR_BGR2GRAY = 0
        mock_cv.RETR_EXTERNAL = 1
        mock_cv.CHAIN_APPROX_SIMPLE = 2

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 Mock")
            temp_pdf = f.name

        try:
            result = detect_psd_images(temp_pdf)
            assert result == []
            assert "skipped" in caplog.text.lower()
        finally:
            os.unlink(temp_pdf)

def test_detect_psd_images_bad_aspect_ratio(mock_convert_from_path, mock_cv2_functions, caplog):
    """Test that pages with bad aspect ratio are skipped."""
    with patch('src.ingest.image_detector.cv2') as mock_cv:
        mock_cv.GaussianBlur.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_cv.Canny.return_value = np.ones((100, 100), dtype=np.uint8) * 255
        # Return enough contours
        mock_cv.findContours.return_value = ([np.zeros((15, 1, 2), dtype=np.int32)], None)
        # Return bounding box with bad aspect ratio (e.g., 100/1 = 100)
        mock_cv.boundingRect.return_value = (10, 10, 100, 1)
        mock_cv.contourArea.return_value = 1000
        mock_cv.cvtColor.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_cv.COLOR_RGB2BGR = 4
        mock_cv.COLOR_BGR2GRAY = 0
        mock_cv.RETR_EXTERNAL = 1
        mock_cv.CHAIN_APPROX_SIMPLE = 2

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 Mock")
            temp_pdf = f.name

        try:
            result = detect_psd_images(temp_pdf)
            assert result == []
            assert "out of range" in caplog.text.lower()
        finally:
            os.unlink(temp_pdf)

def test_save_detection_results():
    """Test saving detection results to JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "results.json"
        test_images = ["img1.png", "img2.png"]
        source_pdf = "test.pdf"

        save_detection_results(source_pdf, test_images, str(output_path))

        assert output_path.exists()
        with open(output_path, 'r') as f:
            data = json.load(f)

        assert data["source_pdf"] == source_pdf
        assert data["detected_images"] == test_images
        assert data["count"] == len(test_images)

@patch('src.ingest.image_detector.convert_from_path')
def test_run_image_detection_pipeline(mock_convert, mock_cv2_functions, temp_pdf_dir, tmp_path):
    """Test the full pipeline execution."""
    # Setup mock
    dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
    mock_convert.return_value = [dummy_img]

    # Create a mock PDF
    mock_pdf = Path(temp_pdf_dir) / "test.pdf"
    mock_pdf.write_text("%PDF-1.4 Mock")

    output_json = str(tmp_path / "output.json")

    run_image_detection_pipeline(temp_pdf_dir, output_json)

    assert os.path.exists(output_json)
    with open(output_json, 'r') as f:
        data = json.load(f)

    assert "detected_images" in data
    assert "count" in data
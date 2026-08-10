"""
Unit tests for the image detection logic in src/ingest/image_detector.py.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

import cv2
import numpy as np
from PIL import Image

from src.ingest.image_detector import detect_psd_images, save_detection_results, OUTPUT_FILE


@pytest.fixture
def temp_pdf_dir(tmp_path):
    """Create a temporary directory for test PDFs."""
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    return pdf_dir


@pytest.fixture
def mock_convert_from_path():
    """Mock pdf2image.convert_from_path to return a simple PIL Image."""
    # Create a dummy RGB image (100x100)
    img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    pil_img = Image.fromarray(img_array, mode='RGB')
    
    return_value = [pil_img]
    
    with patch('src.ingest.image_detector.convert_from_path', return_value=return_value) as mock:
        yield mock


@pytest.fixture
def mock_cv2_functions():
    """Mock cv2 functions to simulate contour detection."""
    # Create a mock contour that satisfies the criteria:
    # - More than 10 points
    # - Aspect ratio within [0.5, 2.0]
    # - Width and Height > 50
    # 20 points, rectangle-like
    contour_points = np.array([
        [10, 10], [90, 10], [90, 90], [10, 90], # 4 points
        [15, 15], [85, 15], [85, 85], [15, 85], # 4 points
        [20, 20], [80, 20], [80, 80], [20, 80], # 4 points
        [25, 25], [75, 25], [75, 75], [25, 75], # 4 points
        [30, 30], [70, 30], [70, 70], [30, 70], # 4 points
    ], dtype=np.int32).reshape((-1, 1, 2))
    
    # Bounding rect: x=10, y=10, w=80, h=80 -> aspect ratio = 1.0
    bounding_rect = (10, 10, 80, 80)
    
    with patch('src.ingest.image_detector.cv2.Canny', return_value=np.zeros((100, 100), dtype=np.uint8)):
        with patch('src.ingest.image_detector.cv2.findContours', return_value=([contour_points], None)):
            with patch('src.ingest.image_detector.cv2.boundingRect', return_value=bounding_rect):
                with patch('src.ingest.image_detector.cv2.imwrite', return_value=True):
                    yield


def test_detect_psd_images_file_not_found():
    """Test that detect_psd_images returns empty list if file not found."""
    result = detect_psd_images("non_existent_file.pdf")
    assert result == []


@patch('src.ingest.image_detector.Path.exists', return_value=True)
def test_detect_psd_images_success(mock_exists, temp_pdf_dir, mock_convert_from_path, mock_cv2_functions):
    """Test successful detection of PSD images."""
    # Create a dummy PDF file (just needs to exist for the mock)
    dummy_pdf = temp_pdf_dir / "test.pdf"
    dummy_pdf.touch()
    
    with patch('src.ingest.image_detector.OUTPUT_DIR', temp_pdf_dir):
        results = detect_psd_images(str(dummy_pdf))
    
    # Should return a list with one path
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0].endswith("test_page1.png")
    
    # Verify the output file was created
    assert Path(results[0]).exists()


@patch('src.ingest.image_detector.Path.exists', return_value=True)
def test_detect_psd_images_no_contours(mock_exists, temp_pdf_dir, mock_convert_from_path):
    """Test detection when no contours meet the criteria."""
    dummy_pdf = temp_pdf_dir / "test.pdf"
    dummy_pdf.touch()
    
    # Mock findContours to return empty list or contours with < 10 points
    empty_contours = []
    
    with patch('src.ingest.image_detector.cv2.Canny', return_value=np.zeros((100, 100), dtype=np.uint8)):
        with patch('src.ingest.image_detector.cv2.findContours', return_value=(empty_contours, None)):
            with patch('src.ingest.image_detector.OUTPUT_DIR', temp_pdf_dir):
                results = detect_psd_images(str(dummy_pdf))
    
    assert results == []


@patch('src.ingest.image_detector.Path.exists', return_value=True)
def test_detect_psd_images_bad_aspect_ratio(mock_exists, temp_pdf_dir, mock_convert_from_path):
    """Test detection when aspect ratio is out of range."""
    dummy_pdf = temp_pdf_dir / "test.pdf"
    dummy_pdf.touch()
    
    # Create a contour with bad aspect ratio (e.g., 0.1)
    # x=10, y=10, w=10, h=100 -> aspect ratio = 0.1
    contour_points = np.array([
        [10, 10], [20, 10], [20, 110], [10, 110],
        [12, 12], [18, 12], [18, 108], [12, 108],
    ], dtype=np.int32).reshape((-1, 1, 2))
    bounding_rect = (10, 10, 10, 100) # w=10, h=100 -> AR = 0.1
    
    with patch('src.ingest.image_detector.cv2.Canny', return_value=np.zeros((100, 100), dtype=np.uint8)):
        with patch('src.ingest.image_detector.cv2.findContours', return_value=([contour_points], None)):
            with patch('src.ingest.image_detector.cv2.boundingRect', return_value=bounding_rect):
                with patch('src.ingest.image_detector.OUTPUT_DIR', temp_pdf_dir):
                    results = detect_psd_images(str(dummy_pdf))
    
    assert results == []


def test_save_detection_results(tmp_path):
    """Test saving detection results to JSON."""
    test_data = ["/path/to/img1.png", "/path/to/img2.png"]
    output_file = tmp_path / "results.json"
    
    save_detection_results(test_data, output_file)
    
    assert output_file.exists()
    with open(output_file, 'r') as f:
        saved_data = json.load(f)
    
    assert saved_data == test_data

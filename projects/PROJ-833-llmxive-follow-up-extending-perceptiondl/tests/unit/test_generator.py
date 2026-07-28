"""
Unit tests for code/synthetic/generator.py
"""
import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from PIL import Image
import numpy as np

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from synthetic.generator import generate_sample_for_bin, REGION_COUNTS, SAMPLES_PER_BIN

@pytest.fixture
def mock_image():
    """Create a mock PIL Image."""
    img = Image.new('RGB', (512, 512), color='red')
    return img

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "synthetic_output"
    output_dir.mkdir()
    return output_dir

def test_generate_sample_for_bin_success(mock_image, temp_output_dir):
    """Test successful generation of a sample with specific region count."""
    # Mock the dependencies to avoid actual file I/O and complex logic
    with patch('synthetic.generator.place_boxes_with_retry') as mock_place, \
         patch('synthetic.generator.validate_no_overlaps') as mock_validate, \
         patch('synthetic.generator.derive_all_relations') as mock_derive, \
         patch('synthetic.generator.save_image') as mock_save_img, \
         patch('synthetic.generator.save_annotations') as mock_save_ann:
        
        # Setup mocks
        mock_boxes = [{"x": 10, "y": 10, "w": 50, "h": 50}, {"x": 100, "y": 100, "w": 50, "h": 50}]
        mock_place.return_value = (mock_boxes, True)
        mock_validate.return_value = True
        mock_derive.return_value = [{"relation": "left of", "box1": 0, "box2": 1}]
        
        # Execute
        result = generate_sample_for_bin(
            image_id="test_img_001",
            image=mock_image,
            region_count=20,
            output_dir=temp_output_dir
        )
        
        # Assertions
        assert result is not None
        assert result["region_count"] == 20
        assert result["boxes_placed"] == 2
        assert "test_img_001" in result["image_file"]
        assert "test_img_001" in result["json_file"]
        
        # Verify calls
        mock_place.assert_called_once()
        mock_derive.assert_called_once_with(mock_boxes)
        mock_save_img.assert_called_once()
        mock_save_ann.assert_called_once()

def test_generate_sample_for_bin_placement_failure(mock_image, temp_output_dir):
    """Test handling of placement failure."""
    with patch('synthetic.generator.place_boxes_with_retry') as mock_place, \
         patch('synthetic.generator.logger') as mock_logger:
        
        mock_place.return_value = ([], False)
        
        result = generate_sample_for_bin(
            image_id="test_img_fail",
            image=mock_image,
            region_count=50,
            output_dir=temp_output_dir
        )
        
        assert result is None
        mock_logger.warning.assert_called_once()

def test_generate_sample_for_bin_overlap_failure(mock_image, temp_output_dir):
    """Test handling of validation failure (overlaps)."""
    with patch('synthetic.generator.place_boxes_with_retry') as mock_place, \
         patch('synthetic.generator.validate_no_overlaps') as mock_validate, \
         patch('synthetic.generator.logger') as mock_logger:
        
        mock_boxes = [{"x": 10, "y": 10, "w": 50, "h": 50}]
        mock_place.return_value = (mock_boxes, True)
        mock_validate.return_value = False
        
        result = generate_sample_for_bin(
            image_id="test_img_overlap",
            image=mock_image,
            region_count=20,
            output_dir=temp_output_dir
        )
        
        assert result is None
        mock_logger.error.assert_called_once()

def test_region_counts_config():
    """Verify that all required region counts are present."""
    expected_counts = [20, 25, 30, 35, 40, 45, 50]
    assert REGION_COUNTS == expected_counts

def test_samples_per_bin_config():
    """Verify samples per bin configuration."""
    assert SAMPLES_PER_BIN >= 50
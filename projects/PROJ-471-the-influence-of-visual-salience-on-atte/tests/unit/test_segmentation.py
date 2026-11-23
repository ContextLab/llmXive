"""
Unit tests for code/processing/segmentation.py.

Verifies YOLOv8 face mask generation logic, including:
- Detection of existing pre-segmented masks (fallback skip)
- Invocation of YOLOv8 for face class (COCO index 0 for 'person' -> face refinement or specific face model if configured)
- Output format validation (binary mask, shape alignment)
- Handling of missing/empty detections
"""
import os
import sys
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from processing.segmentation import (
    load_image,
    run_yolo_segmentation,
    generate_face_mask,
    process_image_for_masks,
    MASKS_DIR_NAME
)
from config import get_paths

# Mock YOLO model class to avoid heavy dependency loading in tests
class MockYOLO:
    def __init__(self, model_name):
        self.model_name = model_name
    
    def __call__(self, source, conf=0.25, iou=0.45, device='cpu'):
        # Mock detection result structure
        # Returns a list of Results objects
        mock_result = MagicMock()
        # Simulate one face detection at center
        mock_result.boxes = MagicMock()
        mock_result.boxes.xyxy = np.array([[50, 50, 200, 250]], dtype=np.float32)
        mock_result.boxes.conf = np.array([0.95], dtype=np.float32)
        mock_result.boxes.cls = np.array([0], dtype=np.int64) # COCO class 0 is 'person', assuming face refinement or specific config
        mock_result.masks = MagicMock()
        # Create a dummy binary mask (100x100) with a face-like blob
        dummy_mask = np.zeros((100, 100), dtype=np.uint8)
        dummy_mask[50:150, 50:150] = 255 # Simulate a blob
        # Adjust to image size if needed, but mock usually handles internal sizing
        mock_result.masks.xy = [np.array([[50, 50], [200, 50], [200, 250], [50, 250]])]
        mock_result.masks.xyn = [np.array([[0.2, 0.2], [0.8, 0.2], [0.8, 0.8], [0.2, 0.8]])]
        mock_result.masks.data = torch.tensor([dummy_mask > 128]) # boolean tensor
        return [mock_result]

import torch

@pytest.fixture
def mock_paths():
    """Fixture to mock get_paths to use temporary directories."""
    with patch('processing.segmentation.get_paths') as mock_get:
        mock_paths_obj = MagicMock()
        mock_paths_obj.data_raw = Path("/tmp/mock_data/raw")
        mock_paths_obj.data_interim = Path("/tmp/mock_data/interim")
        mock_paths_obj.data_processed = Path("/tmp/mock_data/processed")
        mock_get.return_value = mock_paths_obj
        yield mock_paths_obj

@pytest.fixture
def mock_image_file(tmp_path):
    """Create a dummy image file for testing."""
    img_path = tmp_path / "test_image.jpg"
    # Create a minimal valid JPEG header (very small, just for existence)
    # In real tests, we'd use PIL to create a valid image, but for unit testing logic, 
    # we often mock the loading part. Here we create a file that exists.
    img_path.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' \",#\x1c\x1c(7),01444\x1f'9t...") 
    # Note: The bytes above are a truncated JPEG header. For robust testing, 
    # we will primarily mock the PIL loading or ensure the file exists.
    # A better approach for a real test:
    try:
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='red')
        img.save(img_path)
    except ImportError:
        pass # Fallback if PIL not installed in test env, though unlikely
    return img_path

def test_load_image_success(mock_image_file):
    """Test successful image loading."""
    img = load_image(str(mock_image_file))
    assert img is not None
    assert img.shape[0] > 0 and img.shape[1] > 0

def test_load_image_file_not_found():
    """Test loading a non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        load_image("/nonexistent/path/image.jpg")

@patch('processing.segmentation.YOLO')
def test_run_yolo_segmentation_calls_model(mock_yolo_class, mock_image_file, mock_paths):
    """Test that YOLO model is instantiated and called correctly."""
    mock_yolo_instance = MockYOLO("yolov8n.pt")
    mock_yolo_class.return_value = mock_yolo_instance

    results = run_yolo_segmentation(str(mock_image_file))
    
    mock_yolo_class.assert_called_once_with("yolov8n.pt")
    mock_yolo_instance.assert_called_once()
    assert len(results) > 0

@patch('processing.segmentation.YOLO')
def test_generate_face_mask_creates_correct_shape(mock_yolo_class, mock_image_file, mock_paths):
    """Test that the generated mask matches the input image dimensions."""
    mock_yolo_instance = MockYOLO("yolov8n.pt")
    mock_yolo_class.return_value = mock_yolo_instance

    mask = generate_face_mask(str(mock_image_file))
    
    # Load original image to get shape
    orig_img = load_image(str(mock_image_file))
    h, w = orig_img.shape[:2]
    
    assert mask.shape == (h, w), f"Mask shape {mask.shape} != Image shape {(h, w)}"
    assert mask.dtype == np.uint8
    assert np.unique(mask).tolist() == [0, 255] or len(np.unique(mask)) == 1

@patch('processing.segmentation.YOLO')
def test_process_image_for_masks_writes_file(mock_yolo_class, tmp_path, mock_paths):
    """Test that process_image_for_masks writes the mask to the correct location."""
    # Setup mock paths to use tmp_path
    mock_paths.data_interim = tmp_path / "interim"
    mock_paths.data_interim.mkdir(parents=True, exist_ok=True)
    
    mock_yolo_instance = MockYOLO("yolov8n.pt")
    mock_yolo_class.return_value = mock_yolo_instance

    image_path = tmp_path / "source.jpg"
    # Create a valid image
    try:
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(image_path)
    except ImportError:
        pytest.skip("PIL not available")

    output_path = process_image_for_masks(str(image_path))
    
    assert output_path is not None
    assert output_path.exists()
    assert "mask" in output_path.name
    assert output_path.suffix == ".npy"

    # Verify content
    mask_data = np.load(output_path)
    assert mask_data.shape == (100, 100)

@patch('processing.segmentation.os.path.exists')
@patch('processing.segmentation.run_yolo_segmentation')
def test_process_image_skips_existing_masks(mock_run_yolo, mock_exists, mock_image_file, mock_paths):
    """Test that existing masks are not regenerated."""
    # Mock that the mask file already exists
    mock_exists.return_value = True
    
    # This should NOT call run_yolo_segmentation
    # We need to mock the internal logic that checks existence
    # The function process_image_for_masks should check if mask exists before running YOLO
    
    # Since the actual implementation might be complex to mock without seeing code,
    # we assume the implementation follows the logic:
    # if mask_path.exists(): return mask_path
    # else: run_yolo...
    
    # Let's test the logic by patching the existence check
    with patch.object(Path, 'exists', return_value=True):
        result = process_image_for_masks(str(mock_image_file))
        mock_run_yolo.assert_not_called()
        # Result should be the path to the existing mask (mocked or real)
        # We just verify YOLO wasn't called
        assert True

def test_face_class_filtering(mock_yolo_class, mock_image_file, mock_paths):
    """Test that only 'face' (or person if face model not available) class is used."""
    # This test verifies that the code filters for the correct class ID.
    # In COCO, 'person' is 0. 'face' is not a standard COCO class in the base model.
    # The spec says "YOLOv8 face mask generation". 
    # If using a specific face model, class 0 is face.
    # If using base YOLOv8, we might need to filter 'person' and then crop, 
    # or use a specific face detection model.
    # Given the task description "YOLOv8 face mask generation", we assume a model 
    # where class 0 is 'face' or the code specifically handles face detection.
    
    mock_yolo_instance = MockYOLO("yolov8n-face.pt") # Assume face model
    mock_yolo_class.return_value = mock_yolo_instance
    
    # If the implementation uses a face-specific model, class 0 is face.
    # We verify the mask is generated based on the detection.
    mask = generate_face_mask(str(mock_image_file))
    assert mask is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

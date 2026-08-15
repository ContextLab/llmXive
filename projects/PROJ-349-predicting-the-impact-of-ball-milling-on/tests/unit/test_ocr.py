"""
Unit tests for OCR extraction functionality (T011b).
Tests extract_psd_from_image with mixed units and config flag handling.
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from PIL import Image
import numpy as np

# Import the function to test
from src.ingest.ocr_fallback import extract_psd_from_image
from src.utils.exceptions import DataIngestionError


def test_extract_psd_from_image_handles_mixed_units():
    """
    Test that extract_psd_from_image correctly parses D10 and D50 from a mock image.
    Action 1: Create a mock PNG image containing text "D10: 100um, D50: 500um".
    Action 2: Call extract_psd_from_image with ocr.fallback_enabled=True.
    Verification: Assert returned dict has d10=100.0, d50=500.0.
    """
    # Create a temporary directory for the mock image
    with tempfile.TemporaryDirectory() as temp_dir:
        image_path = os.path.join(temp_dir, "mock_psd.png")
        
        # Create a simple mock image (white background)
        # We will mock the OCR output directly, so the actual image content doesn't matter
        # as long as the file exists and is a valid image.
        img = Image.new('RGB', (200, 100), color='white')
        img.save(image_path)
        
        # Mock config with fallback enabled
        config = {
            'ocr': {
                'fallback_enabled': True
            }
        }
        
        # Mock the easyocr reader and its run method to return the expected text
        # This simulates the OCR engine successfully reading the text from the image
        with patch('src.ingest.ocr_fallback.easyocr.Reader') as MockReader:
            mock_instance = MagicMock()
            # Mock the readtext method to return the specific text we want to parse
            mock_instance.readtext.return_value = [
                (
                    [(10, 10), (50, 10), (50, 30), (10, 30)], # Bounding box
                    "D10: 100um, D50: 500um", # Text content
                    0.99 # Confidence
                )
            ]
            MockReader.return_value = mock_instance
            
            # Call the function
            result = extract_psd_from_image(
                image_path=image_path,
                flagged_entry_id="test_entry_001",
                config=config
            )
            
            # Verify the result
            assert result is not None, "Result should not be None when OCR is enabled and succeeds"
            assert 'd10' in result, "Result should contain 'd10'"
            assert 'd50' in result, "Result should contain 'd50'"
            assert result['d10'] == 100.0, f"Expected d10=100.0, got {result['d10']}"
            assert result['d50'] == 500.0, f"Expected d50=500.0, got {result['d50']}"
            
            # Verify that easyocr was called
            MockReader.assert_called_once()
            mock_instance.readtext.assert_called_once()


def test_extract_psd_from_image_disabled_config():
    """
    Test that extract_psd_from_image handles the case when OCR is disabled.
    Action: Call extract_psd_from_image with ocr.fallback_enabled=False.
    Verification: Assert function raises DataIngestionError or returns None without attempting OCR.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        image_path = os.path.join(temp_dir, "mock_psd.png")
        
        # Create a valid image file
        img = Image.new('RGB', (200, 100), color='white')
        img.save(image_path)
        
        # Mock config with fallback DISABLED
        config = {
            'ocr': {
                'fallback_enabled': False
            }
        }
        
        # Mock easyocr to ensure it is NOT called
        with patch('src.ingest.ocr_fallback.easyocr.Reader') as MockReader:
            # Call the function
            result = extract_psd_from_image(
                image_path=image_path,
                flagged_entry_id="test_entry_002",
                config=config
            )
            
            # Verification: The function should NOT attempt OCR
            MockReader.assert_not_called()
            
            # Verification: The function should return None or raise an error
            # Based on the spec: "Assert function raises DataIngestionError or returns None"
            # We expect None as the standard behavior for a disabled feature that is skipped
            if result is not None:
                # If it returns something, it must be an error state, but spec says return None
                # or raise. Let's assert that if it's not None, it's not a valid data dict.
                # However, the cleanest implementation is to return None.
                assert False, "Expected None when OCR is disabled, but got a result"
            
            # If we reached here, result was None, which satisfies the requirement
            assert result is None, "Function should return None when OCR is disabled"


def test_extract_psd_from_image_ocr_failure():
    """
    Test that extract_psd_from_image handles OCR failure gracefully (logs warning, returns None).
    This ensures the pipeline doesn't crash if OCR fails, per FR-008.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        image_path = os.path.join(temp_dir, "mock_psd.png")
        
        # Create a valid image file
        img = Image.new('RGB', (200, 100), color='white')
        img.save(image_path)
        
        config = {
            'ocr': {
                'fallback_enabled': True
            }
        }
        
        # Mock easyocr to raise an exception (simulating failure)
        with patch('src.ingest.ocr_fallback.easyocr.Reader') as MockReader:
            mock_instance = MagicMock()
            mock_instance.readtext.side_effect = Exception("OCR Engine Failed")
            MockReader.return_value = mock_instance
            
            # Call the function - it should catch the exception and return None
            result = extract_psd_from_image(
                image_path=image_path,
                flagged_entry_id="test_entry_003",
                config=config
            )
            
            # Verify that it handled the failure gracefully (returned None)
            # and did not crash the pipeline
            assert result is None, "Function should return None if OCR fails"
            
            # Verify that easyocr was attempted
            MockReader.assert_called_once()
            mock_instance.readtext.assert_called_once()
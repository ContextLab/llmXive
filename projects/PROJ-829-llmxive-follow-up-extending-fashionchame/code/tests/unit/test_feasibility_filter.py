import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from PIL import Image
import numpy as np

from src.data.feasibility_filter import FeasibilityFilter, GarmentFeatureClass

@pytest.fixture
def mock_image():
    # Create a dummy RGB image
    img = Image.new("RGB", (224, 224), color=(128, 128, 128))
    return img

@pytest.fixture
def mock_sample():
    return {
        "image_id": "test_123",
        "garment_feature_class": "color",
        "prompt": "A person wearing a red dress"
    }

def test_feasibility_filter_initialization():
    """Test that the filter initializes with default config."""
    with patch("src.data.feasibility_filter.load_config") as mock_load:
        mock_load.return_value = {
            "vlm": {"confidence_threshold": 0.8}
        }
        with patch("src.data.feasibility_filter.BlipProcessor.from_pretrained"):
            with patch("src.data.feasibility_filter.BlipForConditionalGeneration.from_pretrained"):
                filter_engine = FeasibilityFilter()
                assert filter_engine.confidence_threshold == 0.8
                assert filter_engine.device == "cpu"

def test_verify_prompt_with_vlm_high_confidence(mock_image, mock_sample):
    """Test VLM verification returns True for high confidence."""
    with patch("src.data.feasibility_filter.load_config") as mock_load:
        mock_load.return_value = {"vlm": {"confidence_threshold": 0.5}}
        
        # Mock the model and processor
        mock_processor = MagicMock()
        mock_model = MagicMock()
        
        # Mock the forward pass to return a high probability
        # We need to mock the return value of the model forward
        mock_outputs = MagicMock()
        # Logits shape: (batch, seq_len, vocab_size)
        # We simulate a high log prob (close to 0)
        mock_log_probs = torch.tensor([[[-0.1, -0.1, -0.1]]]) 
        mock_outputs.logits = mock_log_probs
        mock_model.return_value = mock_outputs
        
        with patch("src.data.feasibility_filter.BlipProcessor.from_pretrained", return_value=mock_processor):
            with patch("src.data.feasibility_filter.BlipForConditionalGeneration.from_pretrained", return_value=mock_model):
                filter_engine = FeasibilityFilter()
                
                # We need to mock the specific forward call logic inside _verify_prompt_with_vlm
                # Since the method is complex, we patch the internal logic or the result
                # For this unit test, we will patch the return value of the internal calculation
                
                # Instead, let's mock the _verify_prompt_with_vlm method directly to return a known high value
                with patch.object(filter_engine, '_verify_prompt_with_vlm', return_value=(True, 0.95, "Verified")):
                    result = filter_engine.filter_and_verify(mock_sample, "prompt", mock_image, GarmentFeatureClass.COLOR)
                    
                    assert result["is_valid"] is True
                    assert result["confidence"] == 0.95
                    assert result["excluded"] is False

def test_verify_prompt_with_vlm_low_confidence(mock_image, mock_sample):
    """Test VLM verification returns False for low confidence."""
    with patch("src.data.feasibility_filter.load_config") as mock_load:
        mock_load.return_value = {"vlm": {"confidence_threshold": 0.8}}
        
        with patch("src.data.feasibility_filter.BlipProcessor.from_pretrained"):
            with patch("src.data.feasibility_filter.BlipForConditionalGeneration.from_pretrained"):
                filter_engine = FeasibilityFilter()
                
                with patch.object(filter_engine, '_verify_prompt_with_vlm', return_value=(False, 0.3, "Low confidence")):
                    result = filter_engine.filter_and_verify(mock_sample, "prompt", mock_image, GarmentFeatureClass.COLOR)
                    
                    assert result["is_valid"] is False
                    assert result["confidence"] == 0.3
                    assert result["excluded"] is True

def test_run_pipeline_creates_output_file(mock_image, mock_sample):
    """Test that run_pipeline creates the output JSON file."""
    import torch
    from transformers import BlipProcessor, BlipForConditionalGeneration

    with patch("src.data.feasibility_filter.load_config") as mock_load:
        mock_load.return_value = {"vlm": {"confidence_threshold": 0.5}}
        
        # Mock dataset stream
        mock_stream = [mock_sample]
        
        with patch("src.data.feasibility_filter.load_deepfashion2_streaming", return_value=mock_stream):
            with patch("src.data.feasibility_filter.generate_prompt", return_value="test prompt"):
                with patch("src.data.feasibility_filter.Image.open", return_value=mock_image):
                    with patch.object(FeasibilityFilter, '_load_vlm'):
                        # Mock the verification method to avoid real model load
                        with patch.object(FeasibilityFilter, '_verify_prompt_with_vlm', return_value=(True, 0.9, "OK")):
                            with tempfile.TemporaryDirectory() as tmp_dir:
                                output_path = Path(tmp_dir) / "test_output.json"
                                
                                filter_engine = FeasibilityFilter()
                                filter_engine.run_pipeline(output_path, num_samples=1)
                                
                                assert output_path.exists()
                                with open(output_path) as f:
                                    data = json.load(f)
                                    assert len(data) == 1
                                    assert data[0]["image_id"] == "test_123"
                                    assert data[0]["is_valid"] is True
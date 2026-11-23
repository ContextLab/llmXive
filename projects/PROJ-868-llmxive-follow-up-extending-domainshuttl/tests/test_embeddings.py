"""
Tests for the DomainShuttle Encoder Wrapper (T011).

These tests verify:
1. The encoder initializes correctly with frozen weights.
2. The extraction logic handles valid inputs.
3. The "FAIL LOUDLY" policy is enforced for missing models or data.
"""

import pytest
import torch
import os
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the module under test
from src.data.embeddings import DomainShuttleEncoder, run_embedding_pipeline

@pytest.fixture
def mock_config():
    """Provides a mock configuration dict."""
    return {
        "model": {"domain_shuttle_id": "mock-model-id"},
        "paths": {}
    }

@pytest.fixture
def temp_data_dir():
    """Creates a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def mock_subjects(temp_data_dir):
    """Creates a list of mock subjects with real temporary image files."""
    from PIL import Image
    
    subjects = []
    for i in range(3):
        img_path = os.path.join(temp_data_dir, f"subject_{i}.jpg")
        # Create a dummy 64x64 RGB image
        img = Image.new('RGB', (64, 64), color=(i*50, i*50, i*50))
        img.save(img_path)
        
        subjects.append({
            "subject_id": f"subj_{i}",
            "data_path": img_path,
            "category": "test"
        })
    return subjects

def test_encoder_initialization_fails_loudly_on_missing_model(mock_config):
    """
    Verifies that the encoder raises an error if the model cannot be loaded.
    This tests the 'FAIL LOUDLY' requirement.
    """
    with patch('src.data.embeddings.AutoModel') as mock_model, \
         patch('src.data.embeddings.AutoFeatureExtractor') as mock_extractor:
        
        # Simulate a failure in loading the model
        mock_model.from_pretrained.side_effect = Exception("Model not found")
        
        with pytest.raises(RuntimeError, match="DomainShuttle model load failed"):
            DomainShuttleEncoder(mock_config)

def test_encoder_initialization_fails_loudly_on_missing_feature_extractor(mock_config):
    """
    Verifies that the encoder raises an error if the feature extractor fails.
    """
    with patch('src.data.embeddings.AutoModel') as mock_model, \
         patch('src.data.embeddings.AutoFeatureExtractor') as mock_extractor:
        
        mock_model.from_pretrained.return_value = MagicMock()
        mock_extractor.from_pretrained.side_effect = FileNotFoundError("Extractor missing")
        
        with pytest.raises(RuntimeError, match="DomainShuttle model load failed"):
            DomainShuttleEncoder(mock_config)

@patch('src.data.embeddings.AutoModel')
@patch('src.data.embeddings.AutoFeatureExtractor')
def test_extract_embeddings_success(mock_extractor_cls, mock_model_cls, mock_subjects, mock_config):
    """
    Verifies that embeddings are extracted correctly for valid subjects.
    """
    # Setup mocks
    mock_model_instance = MagicMock()
    mock_model_instance.parameters.return_value = []
    mock_model_instance.to.return_value = mock_model_instance
    mock_model_instance.eval.return_value = mock_model_instance
    mock_model_cls.from_pretrained.return_value = mock_model_instance

    mock_extractor_instance = MagicMock()
    mock_extractor_cls.from_pretrained.return_value = mock_extractor_instance

    # Mock the feature extraction to return dummy tensors
    def mock_preprocess(images, return_tensors):
        return {"pixel_values": torch.randn(1, 3, 64, 64)}
    mock_extractor_instance.return_value = mock_preprocess

    # Mock the model output
    mock_output = MagicMock()
    mock_output.last_hidden_state = torch.randn(1, 1, 768) # Batch, Seq, Dim
    mock_model_instance.return_value = mock_output

    # Create encoder
    encoder = DomainShuttleEncoder(mock_config)

    # Extract
    embeddings = encoder.extract_embeddings(mock_subjects)

    # Assertions
    assert len(embeddings) == 3
    assert "subj_0" in embeddings
    assert "subj_1" in embeddings
    assert "subj_2" in embeddings
    assert isinstance(embeddings["subj_0"], torch.Tensor)
    assert embeddings["subj_0"].shape[0] == 768 # Expected dimension

def test_extract_embeddings_fails_loudly_on_missing_data(mock_config, temp_data_dir):
    """
    Verifies that the encoder raises FileNotFoundError if a subject's data is missing.
    """
    # Setup mocks for model loading (success)
    with patch('src.data.embeddings.AutoModel') as mock_model, \
         patch('src.data.embeddings.AutoFeatureExtractor') as mock_extractor:
        
        mock_model_instance = MagicMock()
        mock_model_instance.parameters.return_value = []
        mock_model_instance.to.return_value = mock_model_instance
        mock_model_instance.eval.return_value = mock_model_instance
        mock_model_cls.from_pretrained.return_value = mock_model_instance
        
        mock_extractor_cls.from_pretrained.return_value = MagicMock()

        encoder = DomainShuttleEncoder(mock_config)

        # Create a subject with a non-existent path
        bad_subject = [
            {"subject_id": "bad_subj", "data_path": "/nonexistent/path/image.jpg"}
        ]

        with pytest.raises(FileNotFoundError, match="Subject data file missing"):
            encoder.extract_embeddings(bad_subject)

def test_run_embedding_pipeline_creates_files(mock_subjects, temp_data_dir):
    """
    Verifies that the pipeline script saves .pt files to the output directory.
    """
    output_dir = os.path.join(temp_data_dir, "output")
    
    # Mock the entire encoder class to avoid real model loading overhead
    # and ensure deterministic behavior for the file I/O test
    with patch('src.data.embeddings.DomainShuttleEncoder') as MockEncoder:
        mock_instance = MagicMock()
        # Return mock tensors
        mock_instance.extract_embeddings.return_value = {
            "subj_0": torch.randn(768),
            "subj_1": torch.randn(768),
            "subj_2": torch.randn(768)
        }
        MockEncoder.return_value = mock_instance

        result_dir = run_embedding_pipeline(mock_subjects, output_dir)

        # Check directory exists
        assert os.path.exists(result_dir)
        
        # Check files were created
        assert os.path.exists(os.path.join(result_dir, "subj_0_embedding.pt"))
        assert os.path.exists(os.path.join(result_dir, "subj_1_embedding.pt"))
        assert os.path.exists(os.path.join(result_dir, "subj_2_embedding.pt"))
        
        # Verify content can be loaded
        loaded_tensor = torch.load(os.path.join(result_dir, "subj_0_embedding.pt"))
        assert isinstance(loaded_tensor, torch.Tensor)
        assert loaded_tensor.shape[0] == 768

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
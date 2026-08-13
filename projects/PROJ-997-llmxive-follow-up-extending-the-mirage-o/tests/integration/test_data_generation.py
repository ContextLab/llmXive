"""
T011: Integration test for data streaming and schema validation.
Tests the T015 dataset generation pipeline with mocked components.
"""
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
import torch

from src.cli.generate_dataset import main, process_sample
from src.services.feature_extractor import FeatureResult
from src.services.quantized_inference import InferenceResult

@pytest.fixture
def mock_dataset_stream():
    """Mock dataset stream for testing."""
    return iter([
        {"text": "Sample prompt 1"},
        {"text": "Sample prompt 2"},
        {"text": "Sample prompt 3"},
    ])

@pytest.fixture
def mock_feature_result():
    """Mock feature extraction result."""
    return FeatureResult(
        gradient_norm=0.5,
        local_curvature=0.3,
        logits=torch.randn(1, 10, 128),
        input_ids=torch.randint(0, 1000, (1, 10))
    )

@pytest.fixture
def mock_inference_result():
    """Mock quantized inference result."""
    return InferenceResult(
        logits=torch.randn(1, 5, 128),
        generated_text="Generated text",
        success=True
    )

@pytest.mark.integration
def test_process_sample_success(
    mock_feature_result,
    mock_inference_result
):
    """Test successful sample processing."""
    sample = {"text": "Test prompt"}
    
    with patch('src.cli.generate_dataset.extract_features_for_sample', return_value=mock_feature_result), \
         patch('src.cli.generate_dataset.run_quantized_inference', return_value=mock_inference_result):
        
        result = process_sample(
            sample=sample,
            tokenizer=None,
            model=None,
            quantized_models={"INT4": MagicMock()},
            quantization_level="INT4"
        )
        
        assert result is not None
        assert "input_id" in result
        assert "gradient_norms" in result
        assert "local_curvature" in result
        assert "calculated_kl_divergence" in result
        assert "quantization_level" in result
        assert result["quantization_level"] == "INT4"

@pytest.mark.integration
def test_process_sample_feature_extraction_failure():
    """Test sample processing when feature extraction fails."""
    sample = {"text": "Test prompt"}
    
    with patch('src.cli.generate_dataset.extract_features_for_sample', return_value=None):
        result = process_sample(
            sample=sample,
            tokenizer=None,
            model=None,
            quantized_models={"INT4": MagicMock()},
            quantization_level="INT4"
        )
        
        assert result is None

@pytest.mark.integration
def test_process_sample_inference_failure(mock_feature_result):
    """Test sample processing when quantized inference fails."""
    sample = {"text": "Test prompt"}
    
    with patch('src.cli.generate_dataset.extract_features_for_sample', return_value=mock_feature_result), \
         patch('src.cli.generate_dataset.run_quantized_inference', return_value=None):
        
        result = process_sample(
            sample=sample,
            tokenizer=None,
            model=None,
            quantized_models={"INT4": MagicMock()},
            quantization_level="INT4"
        )
        
        assert result is None

@pytest.mark.integration
def test_main_creates_parquet_file(
    mock_dataset_stream,
    mock_feature_result,
    mock_inference_result,
    tmp_path
):
    """Test that main() creates the expected parquet file."""
    # Patch dependencies
    with patch('src.cli.generate_dataset.load_config', return_value={"DATASET_ID": "test"}), \
         patch('src.cli.generate_dataset.get_dataset_id', return_value="test"), \
         patch('src.cli.generate_dataset.get_model_path', return_value="/fake/path"), \
         patch('src.cli.generate_dataset.load_model_and_tokenizer', return_value=(MagicMock(), MagicMock())), \
         patch('src.cli.generate_dataset.load_quantized_model', return_value=MagicMock()), \
         patch('src.cli.generate_dataset.load_dataset_streaming', return_value=mock_dataset_stream), \
         patch('src.cli.generate_dataset.extract_features_for_sample', return_value=mock_feature_result), \
         patch('src.cli.generate_dataset.run_quantized_inference', return_value=mock_inference_result), \
         patch('src.cli.generate_dataset.OUTPUT_DIR', tmp_path), \
         patch('src.cli.generate_dataset.OUTPUT_FILE', tmp_path / "training_sample.parquet"):
        
        df = main()
        
        # Verify output file exists
        output_file = tmp_path / "training_sample.parquet"
        assert output_file.exists()
        
        # Verify DataFrame structure
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "input_id" in df.columns
        assert "gradient_norms" in df.columns
        assert "local_curvature" in df.columns
        assert "quantized_logits" in df.columns
        assert "calculated_kl_divergence" in df.columns
        assert "quantization_level" in df.columns

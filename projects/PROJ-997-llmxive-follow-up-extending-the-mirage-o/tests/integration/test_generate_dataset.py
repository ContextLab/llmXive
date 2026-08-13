"""
Integration test for the dataset generation pipeline (T015).
Verifies that the pipeline runs, produces output, and the schema is correct.
"""
import os
import sys
import tempfile
import shutil
import pytest
import pandas as pd
from pathlib import Path

# Mock the heavy dependencies to avoid needing actual models for the test
# This test verifies the *orchestration* logic, not the model weights.
from unittest.mock import patch, MagicMock, PropertyMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.cli.generate_dataset import run_generation_pipeline, GenerationStats
from src.services.feature_extractor import FeatureResult
from src.services.quantized_inference import InferenceResult


@pytest.fixture
def mock_env():
    """Mock environment variables and config."""
    with patch('src.config.env_config.load_config') as mock_load:
        mock_load.return_value = {
            "MODEL_PATH": "/fake/model/path",
            "DATASET_ID": "gsm8k"
        }
        yield mock_load


@pytest.fixture
def mock_models():
    """Mock the model loading functions."""
    with patch('src.cli.generate_dataset.AutoModelForCausalLM') as mock_fp_model, \
         patch('src.cli.generate_dataset.AutoTokenizer') as mock_tokenizer, \
         patch('src.services.quantized_inference.load_quantized_model') as mock_q_model:

        # Mock Full Precision Model
        mock_fp_instance = MagicMock()
        mock_fp_instance.device = "cpu"
        mock_fp_instance.to.return_value = mock_fp_instance
        mock_fp_model.from_pretrained.return_value = mock_fp_instance

        # Mock Tokenizer
        mock_tok_instance = MagicMock()
        mock_tok_instance.pad_token = None
        mock_tok_instance.eos_token = "<eos>"
        mock_tok_instance.return_value = {"input_ids": [[1, 2, 3]], "attention_mask": [[1, 1, 1]]}
        mock_tokenizer.from_pretrained.return_value = mock_tok_instance

        # Mock Quantized Model
        mock_q_instance = MagicMock()
        mock_q_model.return_value = mock_q_instance

        yield {
            "fp_model": mock_fp_instance,
            "tokenizer": mock_tok_instance,
            "q_model": mock_q_instance
        }


@pytest.fixture
def mock_dataset_stream():
    """Mock the dataset streaming."""
    mock_sample = {
        "id": "test-123",
        "question": "If I have 5 apples and eat 2, how many are left?",
        "answer": "3"
    }
    def stream_generator():
        yield mock_sample
        yield mock_sample
        yield mock_sample
    return stream_generator


@patch('src.cli.generate_dataset.load_dataset_streaming')
@patch('src.cli.generate_dataset.extract_features_for_sample')
@patch('src.cli.generate_dataset.run_quantized_inference')
@patch('src.cli.generate_dataset.compute_kl_divergence')
def test_pipeline_execution_and_output(
    mock_kl,
    mock_inf,
    mock_feat,
    mock_stream_loader,
    mock_models,
    mock_env
):
    """Test that the pipeline runs and produces a valid Parquet file."""
    
    # Setup mocks
    mock_stream_loader.return_value = mock_dataset_stream()
    
    # Mock Feature Result
    mock_feat_result = MagicMock(spec=FeatureResult)
    mock_feat_result.gradient_norms = 1.5
    mock_feat_result.local_curvature = 0.2
    mock_feat_result.full_precision_logits = [[0.1, 0.2, 0.3]] # Mock tensor-like
    mock_feat.return_value = mock_feat_result

    # Mock Inference Result
    mock_inf_result = MagicMock(spec=InferenceResult)
    mock_inf_result.logits = [[0.1, 0.2, 0.3]]
    mock_inf.return_value = mock_inf_result

    # Mock KL Divergence
    mock_kl.return_value = 0.05

    # Run pipeline
    stats = run_generation_pipeline(max_samples=3, chunk_size=2)

    # Assertions on Stats
    assert stats.processed_samples == 3
    assert stats.skipped_samples == 0
    assert stats.error_samples == 0
    assert os.path.exists("data/processed/training_sample.parquet")

    # Verify Output Schema
    df = pd.read_parquet("data/processed/training_sample.parquet")
    required_columns = [
        "input_id", "gradient_norms", "local_curvature", 
        "quantized_logits", "calculated_kl_divergence", "quantization_level"
    ]
    assert list(df.columns) == required_columns
    
    # Verify Data Types and Content
    assert len(df) == 3 * 3 # 3 samples * 3 quantization levels (int4, int8, fp8)
    assert df["quantization_level"].nunique() == 3
    assert df["calculated_kl_divergence"].min() >= 0.0

    # Cleanup
    if os.path.exists("data/processed/training_sample.parquet"):
        os.remove("data/processed/training_sample.parquet")
    if os.path.exists("logs/pipeline.log"):
        os.remove("logs/pipeline.log")
    if os.path.exists("data/processed/tmp_chunks"):
        shutil.rmtree("data/processed/tmp_chunks")

def test_pipeline_empty_dataset(mock_models, mock_env):
    """Test handling of an empty dataset."""
    with patch('src.cli.generate_dataset.load_dataset_streaming') as mock_stream:
        mock_stream.return_value = iter([]) # Empty iterator
        
        stats = run_generation_pipeline(max_samples=0)
        
        assert stats.processed_samples == 0
        assert not os.path.exists("data/processed/training_sample.parquet")
        
        # Cleanup
        if os.path.exists("logs/pipeline.log"):
            os.remove("logs/pipeline.log")
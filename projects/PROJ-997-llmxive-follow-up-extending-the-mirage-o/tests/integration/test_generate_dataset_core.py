"""
Integration tests for T015b: generate_dataset_core.py

Tests the core logic of feature extraction, quantized inference, and KL calculation.
"""
import pytest
import torch
from unittest.mock import MagicMock, patch
import numpy as np

from src.cli.generate_dataset_core import (
    process_single_sample,
    check_global_level_coverage,
    run_core_generation,
    SampleResult
)
from src.services.feature_extractor import FeatureResult
from src.services.quantized_inference import InferenceResult
from src.models.entities import TrainingSample

@pytest.fixture
def mock_tokenizer():
    mock = MagicMock()
    mock.return_value = {"input_ids": torch.tensor([[1, 2, 3]])}
    return mock

@pytest.fixture
def mock_model_fp():
    mock = MagicMock()
    # Mock output to return logits
    output = MagicMock()
    output.logits = torch.randn(1, 3, 1000) # batch, seq, vocab
    mock.return_value = output
    return mock

@pytest.fixture
def sample_data():
    return {
        "id": "test_sample_001",
        "prompt": "What is 2+2?"
    }

def test_process_single_sample_success(
    mock_tokenizer,
    mock_model_fp,
    sample_data
):
    """Test successful processing of a single sample."""
    with patch("src.cli.generate_dataset_core.extract_features_for_sample") as mock_fe, \
         patch("src.cli.generate_dataset_core.run_quantized_inference") as mock_qi:

        # Mock Feature Extraction
        mock_fe.return_value = FeatureResult(
            gradient_norm=0.5,
            local_curvature=0.2,
            full_precision_logits=torch.randn(3, 1000) # seq, vocab
        )

        # Mock Quantized Inference for all levels
        for level in ["INT4", "INT8", "FP8"]:
            mock_qi.return_value = InferenceResult(
                success=True,
                logits=np.random.randn(3, 1000).astype(np.float32),
                error=None
            )

        result = process_single_sample(sample_data, mock_tokenizer, mock_model_fp, "cpu")

        assert result.success is True
        assert result.input_id == "test_sample_001"
        assert result.gradient_norm == 0.5
        assert len(result.results_by_level) == 3
        assert all(level in result.results_by_level for level in ["INT4", "INT8", "FP8"])
        assert all(result.results_by_level[l]["success"] for l in ["INT4", "INT8", "FP8"])
        assert "INT4" in result.kl_divergences

def test_process_single_sample_inference_failure(
    mock_tokenizer,
    mock_model_fp,
    sample_data
):
    """Test handling of inference failure for one level."""
    with patch("src.cli.generate_dataset_core.extract_features_for_sample") as mock_fe, \
         patch("src.cli.generate_dataset_core.run_quantized_inference") as mock_qi:

        mock_fe.return_value = FeatureResult(
            gradient_norm=0.5,
            local_curvature=0.2,
            full_precision_logits=torch.randn(3, 1000)
        )

        # Mock INT4 success, others fail
        def mock_inference_side_effect(prompt, level):
            if level == "INT4":
                return InferenceResult(success=True, logits=np.random.randn(3, 1000).astype(np.float32), error=None)
            else:
                return InferenceResult(success=False, logits=[], error=f"Failed {level}")

        mock_qi.side_effect = mock_inference_side_effect

        result = process_single_sample(sample_data, mock_tokenizer, mock_model_fp, "cpu")

        assert result.success is False # Because not all levels succeeded
        assert result.results_by_level["INT4"]["success"] is True
        assert result.results_by_level["INT8"]["success"] is False
        assert result.results_by_level["FP8"]["success"] is False

def test_check_global_level_coverage_all_success():
    """Test coverage check when all levels succeed."""
    results = [
        SampleResult(
            input_id="1",
            gradient_norm=0.1,
            local_curvature=0.1,
            results_by_level={
                "INT4": {"success": True, "logits": []},
                "INT8": {"success": True, "logits": []},
                "FP8": {"success": True, "logits": []}
            },
            kl_divergences={"INT4": 0.1, "INT8": 0.1, "FP8": 0.1},
            success=True
        )
    ]
    coverage = check_global_level_coverage(results, 1)
    assert all(coverage.values()) is True

def test_check_global_level_coverage_missing_level():
    """Test coverage check when one level is missing for all samples."""
    results = [
        SampleResult(
            input_id="1",
            gradient_norm=0.1,
            local_curvature=0.1,
            results_by_level={
                "INT4": {"success": True, "logits": []},
                "INT8": {"success": True, "logits": []},
                "FP8": {"success": False, "logits": [], "error": "HW not supported"}
            },
            kl_divergences={"INT4": 0.1, "INT8": 0.1, "FP8": None},
            success=False
        ),
        SampleResult(
            input_id="2",
            gradient_norm=0.1,
            local_curvature=0.1,
            results_by_level={
                "INT4": {"success": True, "logits": []},
                "INT8": {"success": True, "logits": []},
                "FP8": {"success": False, "logits": [], "error": "HW not supported"}
            },
            kl_divergences={"INT4": 0.1, "INT8": 0.1, "FP8": None},
            success=False
        )
    ]
    coverage = check_global_level_coverage(results, 2)
    assert coverage["INT4"] is True
    assert coverage["INT8"] is True
    assert coverage["FP8"] is False # Missing for all

def test_run_core_generation():
    """Test the core generation loop."""
    samples = [
        {"id": "1", "prompt": "Test 1"},
        {"id": "2", "prompt": "Test 2"}
    ]
    mock_tokenizer = MagicMock()
    mock_model = MagicMock()

    with patch("src.cli.generate_dataset_core.extract_features_for_sample") as mock_fe, \
         patch("src.cli.generate_dataset_core.run_quantized_inference") as mock_qi:

        mock_fe.return_value = FeatureResult(
            gradient_norm=0.5,
            local_curvature=0.2,
            full_precision_logits=torch.randn(3, 1000)
        )

        mock_qi.return_value = InferenceResult(
            success=True,
            logits=np.random.randn(3, 1000).astype(np.float32),
            error=None
        )

        processed_rows, coverage = run_core_generation(
            samples, mock_tokenizer, mock_model, "cpu"
        )

        assert len(processed_rows) == 2
        assert all(coverage.values()) is True
        assert processed_rows[0]["input_id"] == "1"
        assert processed_rows[1]["input_id"] == "2"
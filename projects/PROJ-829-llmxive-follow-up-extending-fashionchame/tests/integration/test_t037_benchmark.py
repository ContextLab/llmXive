"""
Integration test for Task T037: Full Benchmark Runner.
Tests the complete pipeline execution and report generation.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
import pytest

from src.pipeline.benchmark_runner import run_full_benchmark
from src.data.stratified_subset import load_filtered_manifest, stratify_samples
from src.pipeline.reporter import aggregate_scores_by_class, generate_report
from src.pipeline.manifest import calculate_file_hash

@pytest.fixture
def mock_settings():
    return {
        "memory_trigger_gb": 6.5,
        "latency_threshold_ms": 50,
        "streaming_chunk_size": 100
    }

@pytest.fixture
def mock_filtered_manifest():
    return [
        {
            "id": "sample_001",
            "image_id": "img_001",
            "garment_feature_class": "color",
            "prompt": "A red dress",
            "confidence": 0.95
        },
        {
            "id": "sample_002",
            "image_id": "img_002",
            "garment_feature_class": "pattern",
            "prompt": "A striped shirt",
            "confidence": 0.92
        },
        {
            "id": "sample_003",
            "image_id": "img_003",
            "garment_feature_class": "texture",
            "prompt": "A silk blouse",
            "confidence": 0.88
        },
        {
            "id": "sample_004",
            "image_id": "img_004",
            "garment_feature_class": "color",
            "prompt": "A blue jacket",
            "confidence": 0.91
        },
        {
            "id": "sample_005",
            "image_id": "img_005",
            "garment_feature_class": "pattern",
            "prompt": "A checkered pants",
            "confidence": 0.89
        }
    ]

@pytest.fixture
def mock_adapter():
    adapter = MagicMock()
    adapter.forward = MagicMock(return_value=MagicMock())
    return adapter

@pytest.mark.integration
@patch("src.pipeline.benchmark_runner.load_filtered_manifest")
@patch("src.pipeline.benchmark_runner.stratify_samples")
@patch("src.pipeline.benchmark_runner.load_deepfashion2_streaming")
@patch("src.pipeline.benchmark_runner.run_text_adapter_pipeline_with_bottleneck_analysis")
@patch("src.pipeline.benchmark_runner.load_config")
@patch("src.pipeline.benchmark_runner.TextCrossAttentionAdapter")
def test_run_full_benchmark(
    mock_adapter_class,
    mock_load_config,
    mock_pipeline_run,
    mock_loader,
    mock_stratify,
    mock_load_manifest,
    mock_filtered_manifest,
    mock_settings,
    tmp_path
):
    """Test that the full benchmark runs and generates required outputs."""
    # Setup mocks
    mock_load_manifest.return_value = mock_filtered_manifest
    mock_stratify.return_value = mock_filtered_manifest[:3]  # Return subset
    mock_load_config.return_value = mock_settings
    mock_adapter_class.return_value = mock_adapter

    # Mock pipeline results for each sample
    mock_pipeline_run.side_effect = [
        {"lpips_score": 0.15, "ssim_score": 0.85, "inference_time_ms": 45.0},
        {"lpips_score": 0.22, "ssim_score": 0.78, "inference_time_ms": 48.0},
        {"lpips_score": 0.18, "ssim_score": 0.82, "inference_time_ms": 42.0},
    ]

    # Run benchmark
    output_dir = tmp_path / "processed"
    output_dir.mkdir()
    
    report = run_full_benchmark(subset_size=3, output_dir=output_dir)

    # Verify outputs exist
    assert (output_dir / "stratified_subset_manifest.json").exists()
    assert (output_dir / "raw_fidelity_scores.json").exists()
    assert (output_dir / "fidelity_report.json").exists()
    assert (output_dir / "benchmark_manifest.json").exists()

    # Verify report structure
    assert "mean_lpips" in report
    assert "mean_ssim" in report
    assert "relative_loss" in report
    assert "latency" in report
    assert "significance" in report

    # Verify latency check
    assert report["latency"]["status"] in ["PASS", "FAIL", "UNKNOWN"]
    assert "average_ms" in report["latency"]

@pytest.mark.integration
@patch("src.pipeline.benchmark_runner.load_filtered_manifest")
@patch("src.pipeline.benchmark_runner.stratify_samples")
@patch("src.pipeline.benchmark_runner.load_config")
@patch("src.pipeline.benchmark_runner.TextCrossAttentionAdapter")
@patch("src.pipeline.benchmark_runner.run_text_adapter_pipeline_with_bottleneck_analysis")
def test_benchmark_with_low_confidence_samples(
    mock_pipeline_run,
    mock_adapter_class,
    mock_load_config,
    mock_stratify,
    mock_load_manifest,
    tmp_path
):
    """Test that low confidence samples are handled correctly."""
    manifest_with_low_conf = [
        {"id": "s1", "image_id": "i1", "garment_feature_class": "color", "confidence": 0.95},
        {"id": "s2", "image_id": "i2", "garment_feature_class": "pattern", "confidence": 0.45},  # Low confidence
        {"id": "s3", "image_id": "i3", "garment_feature_class": "texture", "confidence": 0.88},
    ]
    
    mock_load_manifest.return_value = manifest_with_low_conf
    mock_stratify.return_value = [manifest_with_low_conf[0], manifest_with_low_conf[2]]  # Low conf excluded
    mock_load_config.return_value = {"memory_trigger_gb": 6.5, "latency_threshold_ms": 50}
    mock_adapter_class.return_value = MagicMock()
    mock_pipeline_run.return_value = {"lpips_score": 0.15, "ssim_score": 0.85, "inference_time_ms": 40.0}

    output_dir = tmp_path / "processed"
    output_dir.mkdir()
    
    report = run_full_benchmark(subset_size=2, output_dir=output_dir)

    # Should only process high confidence samples
    assert mock_pipeline_run.call_count == 2

@pytest.mark.integration
@patch("src.pipeline.benchmark_runner.load_filtered_manifest")
@patch("src.pipeline.benchmark_runner.stratify_samples")
@patch("src.pipeline.benchmark_runner.load_config")
@patch("src.pipeline.benchmark_runner.TextCrossAttentionAdapter")
@patch("src.pipeline.benchmark_runner.run_text_adapter_pipeline_with_bottleneck_analysis")
def test_benchmark_handles_pipeline_errors(
    mock_pipeline_run,
    mock_adapter_class,
    mock_load_config,
    mock_stratify,
    mock_load_manifest,
    tmp_path
):
    """Test that pipeline errors are handled gracefully."""
    mock_load_manifest.return_value = [
        {"id": "s1", "image_id": "i1", "garment_feature_class": "color"},
        {"id": "s2", "image_id": "i2", "garment_feature_class": "pattern"},
    ]
    mock_stratify.return_value = mock_load_manifest.return_value
    mock_load_config.return_value = {"memory_trigger_gb": 6.5, "latency_threshold_ms": 50}
    mock_adapter_class.return_value = MagicMock()
    
    # First sample succeeds, second fails
    mock_pipeline_run.side_effect = [
        {"lpips_score": 0.15, "ssim_score": 0.85, "inference_time_ms": 40.0},
        Exception("Simulated failure"),
    ]

    output_dir = tmp_path / "processed"
    output_dir.mkdir()
    
    # Should not raise, should continue with successful samples
    report = run_full_benchmark(subset_size=2, output_dir=output_dir)
    
    # Should have processed at least one sample
    assert "mean_lpips" in report

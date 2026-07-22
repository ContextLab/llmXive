import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from main import run_baseline_inference_pipeline, run_flow_coherence_inference_pipeline
from data.models import VideoClip, MetricRecord

@patch('main.load_processed_clips')
@patch('main.run_baseline_inference')
@patch('main.compute_background_stability_score')
@patch('main.compute_ssim')
@patch('main.compute_temporal_gradient_variance')
@patch('main.MemoryProfiler')
def test_baseline_inference_loop(
    mock_profiler,
    mock_grad,
    mock_ssim,
    mock_bss,
    mock_inference,
    mock_load_clips
):
    """Test that baseline inference loop processes clips and writes output."""
    # Setup mocks
    mock_load_clips.return_value = [
        VideoClip(id="clip1", path="fake.mp4", motion_category="Static", flow_field=None, mask=None)
    ]
    mock_inference.return_value = MagicMock(frames=[[1, 2], [3, 4]], fps=30)
    mock_bss.return_value = {"score": 0.9}
    mock_ssim.return_value = {"score": 0.95}
    mock_grad.return_value = {"variance": 0.01}
    
    mock_profiler_instance = MagicMock()
    mock_profiler_instance.get_peak_memory.return_value = 2000
    mock_profiler.return_value = mock_profiler_instance

    # Run
    output_dir = "data/metrics"
    results = run_baseline_inference_pipeline(output_dir=output_dir)

    # Assertions
    assert len(results) == 1
    assert isinstance(results[0], MetricRecord)
    assert results[0].clip_id == "clip1"
    assert results[0].model_variant == "baseline"
    
    # Check files were written
    assert Path(output_dir).exists()
    assert Path(output_dir).joinpath("baseline_results.json").exists()
    assert Path(output_dir).joinpath("baseline_bss.json").exists()
    assert Path(output_dir).joinpath("baseline_ssim.json").exists()
    assert Path(output_dir).joinpath("baseline_grad.json").exists()

@patch('main.load_processed_clips')
@patch('main.run_flow_coherence_inference')
@patch('main.compute_background_stability_score')
@patch('main.compute_ssim')
@patch('main.compute_temporal_gradient_variance')
@patch('main.compute_flow_statistics')
@patch('main.MemoryProfiler')
@patch('main.CheckpointManager')
def test_flow_inference_loop(
    mock_checkpoint_mgr,
    mock_profiler,
    mock_flow_stats,
    mock_grad,
    mock_ssim,
    mock_bss,
    mock_inference,
    mock_load_clips
):
    """Test that flow-coherence inference loop processes clips, handles checkpoints, and writes output."""
    # Setup mocks
    mock_load_clips.return_value = [
        VideoClip(id="clip1", path="fake.mp4", motion_category="Static", flow_field=None, mask=None)
    ]
    
    mock_inference_result = MagicMock()
    mock_inference_result.frames = [[1, 2], [3, 4]]
    mock_inference_result.invalid_flow_count = 0
    mock_inference.return_value = mock_inference_result
    
    mock_bss.return_value = {"score": 0.88}
    mock_ssim.return_value = {"score": 0.92}
    mock_grad.return_value = {"variance": 0.02}
    mock_flow_stats.return_value = {"mean_magnitude": 1.5}

    mock_profiler_instance = MagicMock()
    mock_profiler_instance.get_peak_memory.return_value = 1800
    mock_profiler.return_value = mock_profiler_instance

    mock_checkpoint_instance = MagicMock()
    mock_checkpoint_instance.is_processed.return_value = False
    mock_checkpoint_instance.mark_processed.return_value = None
    mock_checkpoint_mgr.return_value = mock_checkpoint_instance

    # Run
    output_dir = "data/metrics"
    results = run_flow_coherence_inference_pipeline(output_dir=output_dir, checkpoint_id="test_run")

    # Assertions
    assert len(results) == 1
    assert isinstance(results[0], MetricRecord)
    assert results[0].clip_id == "clip1"
    assert results[0].model_variant == "flow_coherence"
    assert results[0].peak_memory == 1800
    
    # Check files were written
    assert Path(output_dir).exists()
    assert Path(output_dir).joinpath("flow_results.json").exists()
    assert Path(output_dir).joinpath("flow_bss.json").exists()
    assert Path(output_dir).joinpath("flow_ssim.json").exists()
    assert Path(output_dir).joinpath("flow_grad.json").exists()
    assert Path(output_dir).joinpath("flow_stats.json").exists()
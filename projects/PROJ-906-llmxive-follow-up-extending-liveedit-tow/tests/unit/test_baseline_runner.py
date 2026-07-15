"""
Unit tests for the baseline inference runner.

Tests the main components of the baseline pipeline without requiring
actual video data or model weights.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
import numpy as np
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.main import load_processed_clips, run_baseline_inference_pipeline
from code.data.models import ProcessedClip, MetricRecord
from code.models.baseline import BaselineInferenceResult

@pytest.fixture
def temp_config():
    """Create a temporary configuration for testing."""
    config = {
        'data_dir': '/tmp/test_data',
        'output_dir': '/tmp/test_output',
        'device': 'cpu',
        'num_clips': 5,
        'clip_length': 10
    }
    return config

@pytest.fixture
def mock_processed_clip():
    """Create a mock processed clip for testing."""
    return ProcessedClip(
        video_id='test_video',
        clip_id='test_clip_001',
        frame_count=10,
        mask_path='/tmp/test_data/mask.npy',
        flow_path='/tmp/test_data/flow.npy',
        motion_category='Static',
        motion_magnitude=0.1,
        processed_frames_path='/tmp/test_data/frames',
        mask_frames_path='/tmp/test_data/masks'
    )

@pytest.fixture
def mock_baseline_result():
    """Create a mock baseline inference result."""
    frames = [np.random.rand(64, 64, 3).astype(np.float32) for _ in range(10)]
    return BaselineInferenceResult(
        edited_frames=frames,
        inference_time_seconds=0.5,
        success=True
    )

def test_load_processed_clips_missing_file():
    """Test that loading clips raises FileNotFoundError when file is missing."""
    with pytest.raises(FileNotFoundError):
        load_processed_clips(Path('/nonexistent/directory'))

def test_load_processed_clips_valid_file():
    """Test loading clips from a valid JSON file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        processed_dir = Path(tmpdir)
        processed_file = processed_dir / "processed_clips.json"
        
        # Create mock data
        mock_data = [
            {
                'video_id': 'video1',
                'clip_id': 'clip1',
                'frame_count': 10,
                'mask_path': '/tmp/mask1.npy',
                'flow_path': '/tmp/flow1.npy',
                'motion_category': 'Static',
                'motion_magnitude': 0.1,
                'processed_frames_path': '/tmp/frames1',
                'mask_frames_path': '/tmp/masks1'
            }
        ]
        
        with open(processed_file, 'w') as f:
            json.dump(mock_data, f)
        
        # Load clips
        clips = load_processed_clips(processed_dir)
        
        assert len(clips) == 1
        assert clips[0].video_id == 'video1'
        assert clips[0].clip_id == 'clip1'
        assert clips[0].frame_count == 10

@patch('code.main.run_baseline_inference')
@patch('code.main.compute_background_stability_score')
@patch('code.main.compute_flow_normalized_ssim')
@patch('code.main.get_memory_usage_mb')
def test_run_baseline_inference_pipeline(
    mock_get_memory,
    mock_flow_ssim,
    mock_bss,
    mock_run_inference,
    mock_processed_clip,
    mock_baseline_result,
    temp_config
):
    """Test the baseline inference pipeline with mocked dependencies."""
    # Setup mocks
    mock_get_memory.return_value = 100.5
    mock_bss.return_value = 0.95
    mock_flow_ssim.return_value = 0.92
    mock_run_inference.return_value = mock_baseline_result
    
    # Create mock model and profiler
    mock_model = MagicMock()
    mock_profiler = MagicMock()
    mock_checkpoint = MagicMock()
    
    # Run pipeline
    metric_record = run_baseline_inference_pipeline(
        config=temp_config,
        clip=mock_processed_clip,
        model=mock_model,
        profiler=mock_profiler,
        checkpoint_manager=mock_checkpoint
    )
    
    # Verify results
    assert isinstance(metric_record, MetricRecord)
    assert metric_record.video_id == 'test_video'
    assert metric_record.clip_id == 'test_clip_001'
    assert metric_record.peak_memory_mb == 100.5
    assert metric_record.avg_bss == 0.95
    assert metric_record.flow_normalized_ssim == 0.92
    assert metric_record.inference_time_seconds == 0.5

@patch('code.main.run_baseline_inference')
def test_run_baseline_inference_pipeline_checkpoint_skip(
    mock_run_inference,
    mock_processed_clip,
    temp_config
):
    """Test that already processed clips are skipped."""
    # Create mock checkpoint manager that reports clip as completed
    mock_checkpoint = MagicMock()
    mock_checkpoint.is_completed.return_value = True
    
    # Setup mock to return a metric record when loading from checkpoint
    mock_metrics_file = Path(temp_config['output_dir']) / 'metrics' / 'test_video_test_clip_001_metrics.json'
    mock_metrics_file.parent.mkdir(parents=True, exist_ok=True)
    
    mock_data = {
        'video_id': 'test_video',
        'clip_id': 'test_clip_001',
        'motion_category': 'Static',
        'motion_magnitude': 0.1,
        'peak_memory_mb': 100.0,
        'inference_time_seconds': 0.5,
        'avg_bss': 0.9,
        'flow_normalized_ssim': 0.85,
        'frame_count': 10,
        'timestamp': '2024-01-01T00:00:00',
        'config_snapshot': temp_config
    }
    
    with open(mock_metrics_file, 'w') as f:
        json.dump(mock_data, f)
    
    mock_checkpoint.get_metrics_file.return_value = mock_metrics_file
    
    # Create mock model and profiler
    mock_model = MagicMock()
    mock_profiler = MagicMock()
    
    # Run pipeline
    metric_record = run_baseline_inference_pipeline(
        config=temp_config,
        clip=mock_processed_clip,
        model=mock_model,
        profiler=mock_profiler,
        checkpoint_manager=mock_checkpoint
    )
    
    # Verify that inference was not run
    mock_run_inference.assert_not_called()
    
    # Verify that the record was loaded from checkpoint
    assert metric_record.video_id == 'test_video'
    assert metric_record.clip_id == 'test_clip_001'
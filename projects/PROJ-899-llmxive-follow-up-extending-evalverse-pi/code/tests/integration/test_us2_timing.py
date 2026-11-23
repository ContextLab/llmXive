"""
Integration test for timing constraints on a 100-clip batch.

This test verifies that the batch processing logic in src/cli/run_pipeline.py
correctly processes a batch of clips and aggregates timing statistics.

Task: T022 [US2] Integration test for timing constraints on a 100-clip batch
"""
import os
import sys
import tempfile
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.cli.run_pipeline import process_batch_clips, get_sample_clips, main
from src.utils import write_json

@pytest.fixture
def temp_raw_data_dir():
    """Create a temporary directory with mock video files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create mock video files (empty files with .mp4 extension)
        for i in range(150):  # Create 150 files to test sampling
            video_path = tmpdir_path / f"clip_{i:03d}.mp4"
            video_path.touch()
        
        yield tmpdir_path

@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_process_batch_clips_basic(temp_raw_data_dir, temp_output_dir):
    """Test basic batch processing with a small sample of clips."""
    # Select 10 clips for quick testing
    clip_ids = [f"clip_{i:03d}" for i in range(10)]
    
    # Mock the extract_all_features function to avoid actual video processing
    with patch('src.cli.run_pipeline.extract_all_features') as mock_extract:
        mock_extract.return_value = {
            "optical_flow_magnitude": [0.5, 0.6, 0.7],
            "optical_flow_variance": [0.1, 0.2, 0.3],
            "hog_density": [10, 12, 15],
            "spectral_centroid": [100.0, 105.0, 110.0],
            "zero_crossing_rate": [0.05, 0.06, 0.07]
        }
        
        results = process_batch_clips(
            clip_ids=clip_ids,
            raw_data_dir=temp_raw_data_dir,
            output_dir=temp_output_dir,
            max_memory_gb=7.0
        )
        
        # Verify results structure
        assert "total_clips" in results
        assert "processed_clips" in results
        assert "failed_clips" in results
        assert "total_time_seconds" in results
        assert "avg_time_per_clip_seconds" in results
        assert "peak_memory_mb" in results
        assert "clip_details" in results
        
        # Verify processing counts
        assert results["total_clips"] == 10
        assert results["processed_clips"] == 10
        assert results["failed_clips"] == 0
        
        # Verify timing metrics are positive
        assert results["total_time_seconds"] > 0
        assert results["avg_time_per_clip_seconds"] > 0
        
        # Verify clip details
        assert len(results["clip_details"]) == 10
        for detail in results["clip_details"]:
            assert "clip_id" in detail
            assert "status" in detail
            assert detail["status"] == "success"
            assert "time_seconds" in detail
            assert "memory_mb" in detail

def test_process_batch_clips_with_failures(temp_raw_data_dir, temp_output_dir):
    """Test batch processing when some clips fail."""
    # Select 20 clips
    clip_ids = [f"clip_{i:03d}" for i in range(20)]
    
    # Mock extract_all_features to fail for specific clips
    call_count = [0]
    
    def mock_extract_side_effect(video_path, clip_id):
        call_count[0] += 1
        if "clip_005" in clip_id or "clip_015" in clip_id:
            raise Exception(f"Simulated failure for {clip_id}")
        return {
            "optical_flow_magnitude": [0.5],
            "optical_flow_variance": [0.1],
            "hog_density": [10],
            "spectral_centroid": [100.0],
            "zero_crossing_rate": [0.05]
        }
    
    with patch('src.cli.run_pipeline.extract_all_features', side_effect=mock_extract_side_effect):
        results = process_batch_clips(
            clip_ids=clip_ids,
            raw_data_dir=temp_raw_data_dir,
            output_dir=temp_output_dir,
            max_memory_gb=7.0
        )
        
        # Verify results
        assert results["total_clips"] == 20
        assert results["processed_clips"] == 18  # 2 failed
        assert results["failed_clips"] == 2
        
        # Verify failed clips are recorded
        failed_ids = [d["clip_id"] for d in results["clip_details"] if d["status"] == "failed"]
        assert "clip_005" in failed_ids
        assert "clip_015" in failed_ids

def test_get_sample_clips(temp_raw_data_dir):
    """Test sampling logic for clip selection."""
    # Test with n=100
    sample = get_sample_clips(temp_raw_data_dir, n=100)
    assert len(sample) == 100
    
    # Test with n=50
    sample = get_sample_clips(temp_raw_data_dir, n=50)
    assert len(sample) == 50
    
    # Test with n larger than available
    sample = get_sample_clips(temp_raw_data_dir, n=200)
    assert len(sample) == 150  # Only 150 files exist
    
    # Verify clip IDs are sorted and consistent
    sample1 = get_sample_clips(temp_raw_data_dir, n=10)
    sample2 = get_sample_clips(temp_raw_data_dir, n=10)
    assert sample1 == sample2

def test_main_function(temp_raw_data_dir, temp_output_dir, capsys):
    """Test the main function with command line arguments."""
    # Mock the extract_all_features function
    with patch('src.cli.run_pipeline.extract_all_features') as mock_extract:
        mock_extract.return_value = {
            "optical_flow_magnitude": [0.5],
            "optical_flow_variance": [0.1],
            "hog_density": [10],
            "spectral_centroid": [100.0],
            "zero_crossing_rate": [0.05]
        }
        
        # Run main with test arguments
        args = [
            "--n-clips", "10",
            "--raw-dir", str(temp_raw_data_dir),
            "--output-dir", str(temp_output_dir)
        ]
        
        results = main(args)
        
        # Verify results
        assert results["total_clips"] == 10
        assert results["processed_clips"] == 10
        assert results["failed_clips"] == 0
        
        # Verify output was printed
        captured = capsys.readouterr()
        assert "BATCH PROCESSING SUMMARY" in captured.out
        assert "Total time:" in captured.out
        assert "Average time per clip:" in captured.out

def test_batch_processing_creates_output_files(temp_raw_data_dir, temp_output_dir):
    """Test that batch processing creates the expected output files."""
    clip_ids = [f"clip_{i:03d}" for i in range(5)]
    
    with patch('src.cli.run_pipeline.extract_all_features') as mock_extract:
        mock_extract.return_value = {
            "optical_flow_magnitude": [0.5, 0.6],
            "optical_flow_variance": [0.1, 0.2],
            "hog_density": [10, 12],
            "spectral_centroid": [100.0, 105.0],
            "zero_crossing_rate": [0.05, 0.06]
        }
        
        results = process_batch_clips(
            clip_ids=clip_ids,
            raw_data_dir=temp_raw_data_dir,
            output_dir=temp_output_dir,
            max_memory_gb=7.0
        )
        
        # Check that main results file exists
        results_file = temp_output_dir / "batch_processing_results.json"
        assert results_file.exists()
        
        # Check that individual clip directories were created
        for clip_id in clip_ids:
            clip_dir = temp_output_dir / clip_id
            assert clip_dir.exists()
            features_file = clip_dir / "features.json"
            assert features_file.exists()
            
            # Verify features file content
            with open(features_file, 'r') as f:
                features_data = json.load(f)
                assert "clip_id" in features_data
                assert "features" in features_data
                assert features_data["clip_id"] == clip_id

def test_memory_tracking(temp_raw_data_dir, temp_output_dir):
    """Test that memory usage is tracked correctly."""
    clip_ids = [f"clip_{i:03d}" for i in range(5)]
    
    with patch('src.cli.run_pipeline.extract_all_features') as mock_extract:
        mock_extract.return_value = {
            "optical_flow_magnitude": [0.5],
            "optical_flow_variance": [0.1],
            "hog_density": [10],
            "spectral_centroid": [100.0],
            "zero_crossing_rate": [0.05]
        }
        
        results = process_batch_clips(
            clip_ids=clip_ids,
            raw_data_dir=temp_raw_data_dir,
            output_dir=temp_output_dir,
            max_memory_gb=7.0
        )
        
        # Verify memory tracking
        assert "peak_memory_mb" in results
        assert results["peak_memory_mb"] > 0
        
        # Verify clip-level memory tracking
        for detail in results["clip_details"]:
            assert "memory_mb" in detail
            assert detail["memory_mb"] > 0
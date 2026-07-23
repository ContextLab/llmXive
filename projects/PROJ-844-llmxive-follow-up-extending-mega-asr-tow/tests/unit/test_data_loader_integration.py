"""
Integration tests for code/data_loader.py verifying stratified sampling
and stress-curve generation workflow.

Dependencies: T010 (US1 stress-curve logic), T012 (distortion engine), T007a-c (data fetching).
"""
import os
import sys
import tempfile
import shutil
import json
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data_loader import (
    get_config,
    stratified_sample,
    generate_stress_curve_for_clip,
    save_stratified_subset,
    process_stress_curves_in_chunks,
    load_stress_curves_streaming
)
from distortion_engine import DistortionVector, generate_all_distortion_vectors

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_stratified_sampling_workflow():
    """
    Integration test: Verify that stratified sampling correctly selects
    a representative subset from a mock dataset based on speaker accents.
    """
    # Setup mock data
    mock_audio_files = [
        {"path": f"audio_{i}.wav", "speaker_id": f"spk_{i%5}", "accent": f"accent_{i%3}"}
        for i in range(100)
    ]
    
    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        output_file = tmp_path / "stratified_subset.json"
        
        # Mock the save function to capture output instead of writing to disk
        # (In real T010/T007 logic, this would write to data/derived/)
        with patch('data_loader.Path') as mock_path_class:
            # Mock the Path object to return our tmp_path
            mock_path_obj = MagicMock()
            mock_path_obj.__truediv__ = lambda self, name: tmp_path / name
            mock_path_obj.exists.return_value = True
            mock_path_obj.mkdir.return_value = None
            mock_path_class.return_value = mock_path_obj
            mock_path_class.side_effect = lambda x: tmp_path / x if isinstance(x, str) else x
            
            # Run stratified sampling
            # We mock the internal logic to return a deterministic subset for verification
            # In a full integration, this would call the real stratified_sample logic
            result = stratified_sample(mock_audio_files, num_samples=20)
            
            # Verify result structure
            assert isinstance(result, list), "Stratified sample must return a list"
            assert len(result) == 20, f"Expected 20 samples, got {len(result)}"
            
            # Verify stratification (each accent should be represented)
            accents = [item.get("accent") for item in result]
            unique_accents = set(accents)
            assert len(unique_accents) == 3, "All 3 accent groups should be represented"
            
            logger.info(f"Stratified sampling verified: {len(unique_accents)} accent groups found in {len(result)} samples")

def test_stress_curve_generation_workflow():
    """
    Integration test: Verify that stress curve generation logic correctly
    applies distortion vectors to an audio clip and returns expected structure.
    """
    # Mock audio clip path
    mock_audio_path = "/mock/path/audio_001.wav"
    
    # Generate a set of distortion vectors (using real logic from T012)
    # We mock the actual audio processing to avoid needing real audio files
    with patch('data_loader.apply_distortion_to_audio') as mock_apply_distortion:
        mock_apply_distortion.return_value = {
            "audio_data": np.array([0.1, 0.2, 0.3]),
            "distortion_params": {"snr": 10, "rt60": 0.5}
        }
        
        with patch('data_loader.asr_inference') as mock_asr:
            mock_asr.return_value = "This is a test hypothesis"
            
            with patch('data_loader.compute_sss') as mock_sss:
                mock_sss.return_value = 0.85
                
                # Generate distortion vectors
                vectors = generate_all_distortion_vectors(
                    snr_range=(5, 20, 3), 
                    rt60_range=(0.1, 0.8, 2)
                )
                
                # Test stress curve generation for first vector
                result = generate_stress_curve_for_clip(mock_audio_path, vectors[0])
                
                # Verify result structure
                assert isinstance(result, dict), "Stress curve result must be a dict"
                assert "clip_id" in result, "Result must contain clip_id"
                assert "distortion_vector" in result, "Result must contain distortion_vector"
                assert "ss_score" in result, "Result must contain semantic similarity score"
                assert "wer" in result, "Result must contain WER"
                
                logger.info(f"Stress curve generation verified: {result['clip_id']} with SSS={result['ss_score']:.2f}")

def test_chunked_processing_workflow():
    """
    Integration test: Verify that chunked processing correctly handles
    large stress curve datasets without OOM errors.
    """
    # Create mock stress curve data
    mock_curves = [
        {
            "clip_id": f"clip_{i}",
            "distortion_vector_id": f"dv_{i%5}",
            "ss_score": 0.9 - (i * 0.01),
            "wer": 0.05 + (i * 0.01)
        }
        for i in range(100)
    ]
    
    batch_size = 10
    processed_count = 0
    
    # Mock the batch processing and disk flush
    with patch('data_loader.save_batch_results') as mock_save:
        mock_save.return_value = None
        
        # Process in chunks
        result = process_stress_curves_in_chunks(mock_curves, batch_size)
        
        # Verify all curves were processed
        processed_count = sum(len(batch) for batch in result)
        assert processed_count == len(mock_curves), f"Expected {len(mock_curves)} processed, got {processed_count}"
        
        # Verify save was called for each batch
        expected_calls = len(mock_curves) // batch_size
        assert mock_save.call_count == expected_calls, f"Expected {expected_calls} save calls, got {mock_save.call_count}"
        
        logger.info(f"Chunked processing verified: {processed_count} curves processed in {expected_calls} batches")

def test_streaming_load_workflow():
    """
    Integration test: Verify that streaming load correctly handles
    large stress curve datasets without loading everything into memory.
    """
    # Create a temporary CSV file with mock stress curve data
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("clip_id,distortion_vector_id,ss_score,wer\n")
        for i in range(1000):
            f.write(f"clip_{i},dv_{i%10},{0.9 - i*0.001},{0.05 + i*0.001}\n")
        temp_file = f.name
    
    try:
        # Test streaming load
        with patch('data_loader.Path') as mock_path:
            mock_path.return_value = Path(temp_file)
            
            # Mock the actual file reading to simulate streaming
            with patch('builtins.open', mock_open_with_data(temp_file)):
                curves = list(load_stress_curves_streaming(Path(temp_file)))
                
                # Verify all curves were loaded
                assert len(curves) == 1000, f"Expected 1000 curves, got {len(curves)}"
                
                # Verify first and last curve structure
                assert curves[0]["clip_id"] == "clip_0"
                assert curves[-1]["clip_id"] == "clip_999"
                
                logger.info(f"Streaming load verified: {len(curves)} curves loaded")
    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)

def mock_open_with_data(filepath):
    """Helper to mock file open for testing."""
    def _open(*args, **kwargs):
        return open(filepath, *args, **kwargs)
    return _open

if __name__ == "__main__":
    # Run tests manually if executed as script
    test_stratified_sampling_workflow()
    test_stress_curve_generation_workflow()
    test_chunked_processing_workflow()
    test_streaming_load_workflow()
    print("All integration tests passed!")

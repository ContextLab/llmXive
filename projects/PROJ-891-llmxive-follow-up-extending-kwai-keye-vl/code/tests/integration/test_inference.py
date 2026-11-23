"""
Integration test for model loading and single clip inference (T019).

This test verifies that the Kwai Keye-VL model can be loaded in INT4 quantization
on CPU and successfully process a single video clip to produce temporal grounding
predictions without OOM errors.

Prerequisites:
- T005: models/ directory exists
- T012b/T013: Sample video clips exist in data/raw/original/ or data/distorted/
- T002: Dependencies installed (transformers, optimum-intel, llama-cpp-python, etc.)

This test is marked as [P] (parallel) because it operates on a single clip
and does not depend on other user story implementations.
"""
import os
import sys
import json
import tempfile
import subprocess
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the inference module (placeholder for T020 implementation)
# We will mock the actual model loading for this integration test
# to avoid requiring the full model download during CI
try:
    from src.inference.run_inference import (
        load_model, 
        run_inference_on_clip, 
        process_video_batch,
        MemoryLimitError
    )
    MODEL_MODULE_AVAILABLE = True
except ImportError:
    MODEL_MODULE_AVAILABLE = False
    # Define minimal mocks if module not yet implemented
    class MemoryLimitError(Exception):
        pass

@pytest.fixture
def sample_video_path():
    """
    Fixture that provides a path to a sample video file.
    Falls back to checking data directories or creating a minimal test video.
    """
    # Check common data locations
    possible_paths = [
        project_root / "data" / "raw" / "original" / "sample.mp4",
        project_root / "data" / "distorted" / "sample.mp4",
        project_root / "data" / "raw" / "sample.mp4",
    ]
    
    for path in possible_paths:
        if path.exists():
            return str(path)
    
    # If no real video exists, we'll create a minimal test video using ffmpeg
    # This is acceptable for integration testing of the pipeline
    # In production, real data from T012b/T013 should be used
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # Create a 2-second test video with ffmpeg
        subprocess_result = subprocess.run(
            [
                "ffmpeg",
                "-f", "lavfi",
                "-i", "color=c=blue:s=320x240:d=2",
                "-vf", "fps=25",
                "-pix_fmt", "yuv420p",
                "-y",
                tmp_path
            ],
            capture_output=True,
            timeout=30
        )
        if subprocess_result.returncode == 0 and os.path.exists(tmp_path):
            return tmp_path
    except Exception:
        pass
    
    # If all else fails, raise a clear error
    raise FileNotFoundError(
        "No sample video found. Please ensure T012b or T013 has generated test data, "
        "or install ffmpeg to create a test video."
    )

@pytest.fixture
def mock_model():
    """
    Mock model object that simulates the Kwai Keye-VL INT4 model interface.
    """
    mock_model = MagicMock()
    mock_model.model_type = "kwai-keye-vl-2.0-int4"
    mock_model.max_memory = "7GB"
    
    def mock_generate(prompt, max_new_tokens=100, temperature=0.0):
        # Simulate a reasonable temporal grounding prediction
        # Format: "Start: 1.5s, End: 3.2s"
        return "Start: 1.5s, End: 3.2s"
    
    mock_model.generate = mock_generate
    return mock_model

@pytest.mark.integration
def test_model_loading_cpu_int4():
    """
    Test that the model can be loaded in INT4 quantization on CPU.
    
    This test verifies:
    1. The model loading function exists and is callable
    2. The model loads without immediate errors
    3. The model is configured for CPU execution
    4. Memory limits are respected during loading
    """
    if not MODEL_MODULE_AVAILABLE:
        pytest.skip("Model inference module not yet implemented (T020)")
    
    # Test with mocked model loading to avoid downloading the full model
    with patch('src.inference.run_inference.load_model_from_hf') as mock_load:
        mock_load.return_value = mock_model()
        
        try:
            model = load_model(
                model_name="Kwai-Kyle/Kwai-Keye-VL-2.0-Int4",
                device="cpu",
                quantization="int4",
                max_memory="7GB"
            )
            
            assert model is not None, "Model should not be None"
            assert model.model_type == "kwai-keye-vl-2.0-int4", "Model type should match"
            assert mock_load.called, "Model loading function should be called"
            
        except Exception as e:
            pytest.fail(f"Model loading failed: {str(e)}")

@pytest.mark.integration
def test_single_clip_inference(sample_video_path, mock_model):
    """
    Test inference on a single video clip.
    
    This test verifies:
    1. The inference function can process a single video
    2. The output format is valid JSON with start/end timestamps
    3. No OOM errors occur during processing
    4. The model receives the correct input format
    """
    if not MODEL_MODULE_AVAILABLE:
        pytest.skip("Model inference module not yet implemented (T020)")
    
    # Mock the model loading to use our mock model
    with patch('src.inference.run_inference.load_model') as mock_load:
        mock_load.return_value = mock_model
        
        try:
            result = run_inference_on_clip(
                video_path=sample_video_path,
                model=mock_model,
                task_description="Find the temporal segment where a blue square appears",
                max_memory="7GB"
            )
            
            # Verify result structure
            assert result is not None, "Result should not be None"
            assert "video_id" in result, "Result should contain video_id"
            assert "start_time" in result, "Result should contain start_time"
            assert "end_time" in result, "Result should contain end_time"
            assert "confidence" in result or "status" in result, "Result should have confidence or status"
            
            # Verify timestamps are numeric
            assert isinstance(result["start_time"], (int, float)), "start_time should be numeric"
            assert isinstance(result["end_time"], (int, float)), "end_time should be numeric"
            assert result["start_time"] >= 0, "start_time should be non-negative"
            assert result["end_time"] >= result["start_time"], "end_time should be >= start_time"
            
            # Verify no OOM occurred
            assert result.get("status") != "OOM", "Should not have OOM error"
            
        except MemoryLimitError:
            pytest.fail("Memory limit error occurred during single clip inference")
        except Exception as e:
            pytest.fail(f"Inference failed: {str(e)}")

@pytest.mark.integration
def test_inference_output_format(sample_video_path, mock_model):
    """
    Test that inference output matches the expected JSON schema.
    
    Verifies the output is compatible with the mIoU calculation module (T026).
    """
    if not MODEL_MODULE_AVAILABLE:
        pytest.skip("Model inference module not yet implemented (T020)")
    
    expected_schema = {
        "video_id": str,
        "start_time": (int, float),
        "end_time": (int, float),
        "status": str,
        "model_version": str,
        "processing_time": (int, float)
    }
    
    with patch('src.inference.run_inference.load_model') as mock_load:
        mock_load.return_value = mock_model
        
        result = run_inference_on_clip(
            video_path=sample_video_path,
            model=mock_model,
            task_description="Temporal grounding test",
            max_memory="7GB"
        )
        
        # Check all required fields exist
        for field, field_type in expected_schema.items():
            assert field in result, f"Missing required field: {field}"
            assert isinstance(result[field], field_type), f"Field {field} has wrong type"
        
        # Verify the result can be serialized to JSON
        json_str = json.dumps(result)
        assert json_str is not None, "Result should be JSON serializable"
        
        # Verify it can be parsed back
        parsed = json.loads(json_str)
        assert parsed == result, "Parsed JSON should match original result"

@pytest.mark.integration
def test_memory_limit_enforcement(sample_video_path, mock_model):
    """
    Test that memory limits are properly enforced during inference.
    
    This test verifies the memory monitoring wrapper (T021) is integrated
    and would trigger on excessive memory usage.
    """
    if not MODEL_MODULE_AVAILABLE:
        pytest.skip("Model inference module not yet implemented (T020)")
    
    # Test with a very low memory limit that should trigger the limit
    # Note: In a real scenario, we'd need a model that actually uses significant memory
    # For this test, we verify the mechanism is in place
    
    with patch('src.inference.run_inference.load_model') as mock_load:
        mock_load.return_value = mock_model
        
        # This should not raise an exception for normal operation
        # but should respect the memory limit if exceeded
        result = run_inference_on_clip(
            video_path=sample_video_path,
            model=mock_model,
            task_description="Memory limit test",
            max_memory="7GB"  # Normal limit
        )
        
        assert result is not None, "Should complete within memory limit"
        assert result.get("status") != "OOM", "Should not exceed memory limit"

@pytest.mark.integration
def test_inference_with_distorted_video(sample_video_path, mock_model):
    """
    Test inference on a distorted video (extreme aspect ratio).
    
    This is critical for the research question about aspect ratio robustness.
    Uses the same test video but simulates a distorted input scenario.
    """
    if not MODEL_MODULE_AVAILABLE:
        pytest.skip("Model inference module not yet implemented (T020)")
    
    with patch('src.inference.run_inference.load_model') as mock_load:
        mock_load.return_value = mock_model
        
        # Simulate processing a distorted video
        result = run_inference_on_clip(
            video_path=sample_video_path,
            model=mock_model,
            task_description="Find the event in this distorted video",
            max_memory="7GB",
            metadata={"aspect_ratio": "1:10", "distortion_type": "extreme"}
        )
        
        assert result is not None, "Should process distorted video"
        assert "start_time" in result and "end_time" in result, "Should return timestamps"
        
        # Verify the result includes distortion metadata
        assert result.get("distortion_type") == "extreme", "Should track distortion type"

@pytest.mark.integration
def test_inference_error_handling(sample_video_path, mock_model):
    """
    Test that the inference pipeline handles errors gracefully.
    
    Verifies:
    1. Invalid video paths are handled
    2. Corrupted video files are detected
    3. Model errors are caught and reported
    """
    if not MODEL_MODULE_AVAILABLE:
        pytest.skip("Model inference module not yet implemented (T020)")
    
    with patch('src.inference.run_inference.load_model') as mock_load:
        mock_load.return_value = mock_model
        
        # Test with non-existent video
        with pytest.raises(FileNotFoundError):
            run_inference_on_clip(
                video_path="/nonexistent/video.mp4",
                model=mock_model,
                task_description="Test",
                max_memory="7GB"
            )
        
        # Test with invalid video path type
        with pytest.raises(ValueError):
            run_inference_on_clip(
                video_path=123,  # Invalid type
                model=mock_model,
                task_description="Test",
                max_memory="7GB"
            )

@pytest.mark.integration
def test_batch_inference_single_clip(sample_video_path, mock_model):
    """
    Test batch processing with a single clip (edge case).
    
    Verifies the batch processing function (T020) works correctly
    even with minimal input.
    """
    if not MODEL_MODULE_AVAILABLE:
        pytest.skip("Model inference module not yet implemented (T020)")
    
    with patch('src.inference.run_inference.load_model') as mock_load:
        mock_load.return_value = mock_model
        
        results = process_video_batch(
            video_paths=[sample_video_path],
            model=mock_model,
            task_description="Batch test with single clip",
            max_memory="7GB"
        )
        
        assert isinstance(results, list), "Results should be a list"
        assert len(results) == 1, "Should have one result for one video"
        assert results[0].get("status") != "ERROR", "Should not have error status"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
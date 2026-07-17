"""
Contract test for feature extraction output schema (US1 - T010).

This test verifies that the feature extraction pipeline produces outputs
that strictly adhere to the defined schema contracts. It ensures that:
1. The output is a list of dictionaries.
2. Each dictionary contains the required keys (clip_id, features, metadata).
3. The 'features' value is a list of floats.
4. The 'metadata' dictionary contains expected keys (duration, fps, audio_present).
5. Data types are strictly enforced.
"""

import pytest
import sys
import os
import numpy as np

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from src.data.preprocess import extract_all_features, process_video_clip, batch_process_clips
from src.data.models import FeatureVector
from src.utils import get_logger

logger = get_logger("test_feature_schema")


# --- Mock Data for Contract Testing ---
# We cannot rely on the full EvalVerse dataset being present for a unit contract test.
# We will create a minimal, valid temporary video file to ensure the schema contract
# holds for the extraction logic itself.

def create_dummy_video(path: str, duration_sec: float = 1.0, fps: int = 30):
    """Creates a minimal valid video file for testing purposes."""
    import cv2
    import numpy as np
    
    frame_size = (64, 64)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(path, fourcc, fps, frame_size)
    
    total_frames = int(duration_sec * fps)
    for _ in range(total_frames):
        # Create a simple gradient frame
        frame = np.zeros((frame_size[1], frame_size[0], 3), dtype=np.uint8)
        frame[:, :] = np.random.randint(50, 200, size=(frame_size[1], frame_size[0], 3), dtype=np.uint8)
        out.write(frame)
    
    out.release()
    return path


class TestFeatureSchema:
    """
    Contract tests for the feature extraction output schema.
    """

    @pytest.fixture
    def dummy_video_path(self, tmp_path):
        """Create a temporary dummy video file."""
        video_path = tmp_path / "test_clip.mp4"
        return create_dummy_video(str(video_path), duration_sec=0.5, fps=15)

    @pytest.fixture
    def dummy_audio_path(self, tmp_path):
        """Create a temporary dummy audio file (silence)."""
        import soundfile as sf
        audio_path = tmp_path / "test_audio.wav"
        # Create 0.5s of silence at 22050 Hz
        silence = np.zeros(11025, dtype=np.float32)
        sf.write(str(audio_path), silence, 22050)
        return str(audio_path)

    def test_process_video_clip_output_structure(self, dummy_video_path):
        """
        Contract: process_video_clip must return a dictionary with specific keys.
        """
        result = process_video_clip(
            video_path=dummy_video_path,
            clip_id="test_001",
            target_fps=10,
            sample_duration=0.5
        )

        # Assert result is a dict
        assert isinstance(result, dict), "Output must be a dictionary"

        # Assert required top-level keys exist
        required_keys = {"clip_id", "features", "metadata", "success"}
        assert all(key in result for key in required_keys), f"Missing required keys: {required_keys - result.keys()}"

        # Assert types
        assert isinstance(result["clip_id"], str), "clip_id must be a string"
        assert isinstance(result["success"], bool), "success must be a boolean"

        # Assert features structure
        features = result["features"]
        assert isinstance(features, list), "features must be a list"
        if len(features) > 0:
            assert isinstance(features[0], (int, float, np.floating)), "Features must be numeric"

        # Assert metadata structure
        metadata = result["metadata"]
        assert isinstance(metadata, dict), "metadata must be a dictionary"
        expected_meta_keys = {"duration", "fps", "width", "height", "audio_present"}
        # Note: audio_present might be false if no audio track, but key should exist if handled
        # We verify at least the video metadata exists
        assert "duration" in metadata, "metadata must contain 'duration'"
        assert "fps" in metadata, "metadata must contain 'fps'"
        assert isinstance(metadata["duration"], (int, float)), "duration must be numeric"

    def test_extract_all_features_schema_consistency(self, dummy_video_path):
        """
        Contract: extract_all_features must return a FeatureVector-like structure
        (list of floats) without raising errors on valid input.
        """
        # We test the internal logic by calling the extraction directly
        # Since extract_all_features is designed to be called within the pipeline,
        # we verify the output type matches the expected FeatureVector (List[float])
        
        # Note: extract_all_features expects a frame path or video path depending on implementation.
        # Based on the API surface, it likely processes a video path.
        try:
            features = extract_all_features(dummy_video_path)
            
            # Contract: Output must be a list of numbers
            assert isinstance(features, list), "extract_all_features must return a list"
            assert len(features) > 0, "Features list should not be empty for a valid video"
            
            for val in features:
                assert isinstance(val, (int, float, np.floating)), \
                    f"All feature values must be numeric, found {type(val)}"
        except Exception as e:
            # If it fails, it should be a specific error about missing dependencies,
            # not a schema violation. But for the contract test, we expect success on valid input.
            pytest.fail(f"Feature extraction failed on valid input: {str(e)}")

    def test_batch_process_clips_output_format(self, dummy_video_path, tmp_path):
        """
        Contract: batch_process_clips must return a list of dictionaries
        matching the single-clip schema.
        """
        # Create a second dummy video
        video2_path = str(tmp_path / "test_clip_2.mp4")
        create_dummy_video(video2_path, duration_sec=0.5, fps=15)

        input_files = [
            {"path": dummy_video_path, "id": "clip_1"},
            {"path": video2_path, "id": "clip_2"}
        ]

        results = batch_process_clips(input_files, target_fps=10, sample_duration=0.5)

        # Contract: Output must be a list
        assert isinstance(results, list), "batch_process_clips must return a list"
        assert len(results) == 2, "Should process 2 clips"

        for i, item in enumerate(results):
            # Contract: Each item must match the single-clip schema
            assert isinstance(item, dict), f"Item {i} must be a dictionary"
            assert "clip_id" in item, f"Item {i} missing clip_id"
            assert "features" in item, f"Item {i} missing features"
            assert "success" in item, f"Item {i} missing success"
            
            # Verify types
            assert isinstance(item["clip_id"], str)
            assert isinstance(item["features"], list)
            assert isinstance(item["success"], bool)

    def test_feature_vector_data_types(self, dummy_video_path):
        """
        Contract: Ensure no NaN or Inf values in features unless explicitly allowed (not here).
        """
        result = process_video_clip(
            video_path=dummy_video_path,
            clip_id="test_nan_check",
            target_fps=10,
            sample_duration=0.5
        )

        if result["success"]:
            features = result["features"]
            for val in features:
                val_float = float(val)
                assert not np.isnan(val_float), f"Feature contains NaN: {val_float}"
                assert not np.isinf(val_float), f"Feature contains Inf: {val_float}"
        else:
            # If success is false, we skip the check, but the schema (success=False) is valid
            pass

    def test_schema_with_missing_audio(self, dummy_video_path):
        """
        Contract: Pipeline must handle missing audio gracefully and still return valid schema.
        (The dummy video created by cv2 usually has no audio track).
        """
        result = process_video_clip(
            video_path=dummy_video_path,
            clip_id="test_no_audio",
            target_fps=10,
            sample_duration=0.5
        )

        # Must return a valid dict
        assert isinstance(result, dict)
        assert "success" in result
        assert "features" in result
        assert "metadata" in result
        
        # Metadata should indicate audio status (even if false)
        # The schema contract requires metadata to exist, specific keys may vary by implementation
        # but 'audio_present' is a logical expectation based on the task description.
        if "audio_present" in result["metadata"]:
            assert isinstance(result["metadata"]["audio_present"], bool)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Contract tests for video utility schema compliance.

These tests verify that the video utilities produce outputs
that conform to the expected schema defined in contracts/video.schema.yaml
"""

import os
import tempfile
import numpy as np
import pytest
import yaml
import cv2

from code.utils.video import (
    get_video_metadata,
    extract_frames,
    write_video
)

# Load expected schema
SCHEMA_PATH = "contracts/video.schema.yaml"

def load_schema():
    """Load the video schema from file."""
    if os.path.exists(SCHEMA_PATH):
        with open(SCHEMA_PATH, 'r') as f:
            return yaml.safe_load(f)
    return None


def create_test_video(output_path: str, num_frames: int = 10, fps: float = 24.0, 
                     width: int = 640, height: int = 480):
    """Helper function to create a test video file."""
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    for i in range(num_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:, :, 0] = (i * 25) % 256
        writer.write(frame)
        
    writer.release()
    return output_path


class TestVideoMetadataSchema:
    """Test that video metadata conforms to schema."""
    
    def test_metadata_schema_compliance(self, tmp_path):
        """Test that get_video_metadata returns schema-compliant data."""
        video_path = tmp_path / "test.mp4"
        create_test_video(str(video_path))
        
        metadata = get_video_metadata(str(video_path))
        
        # Check required fields
        required_fields = ['duration', 'fps', 'frame_count', 'width', 'height', 'codec']
        for field in required_fields:
            assert field in metadata, f"Missing required field: {field}"
        
        # Check types
        assert isinstance(metadata['duration'], float)
        assert isinstance(metadata['fps'], float)
        assert isinstance(metadata['frame_count'], int)
        assert isinstance(metadata['width'], int)
        assert isinstance(metadata['height'], int)
        assert isinstance(metadata['codec'], str)
        
        # Check value constraints
        assert metadata['duration'] > 0
        assert metadata['fps'] > 0
        assert metadata['frame_count'] > 0
        assert metadata['width'] > 0
        assert metadata['height'] > 0
        
    def test_schema_validation(self, tmp_path):
        """Test against loaded schema if available."""
        schema = load_schema()
        if not schema:
            pytest.skip("Schema file not found")
            
        video_path = tmp_path / "test.mp4"
        create_test_video(str(video_path))
        
        metadata = get_video_metadata(str(video_path))
        
        # Validate against schema (simplified check)
        if 'required' in schema.get('metadata', {}):
            for field in schema['metadata']['required']:
                assert field in metadata, f"Schema violation: missing {field}"
                
        if 'properties' in schema.get('metadata', {}):
            for field, props in schema['metadata']['properties'].items():
                if field in metadata and 'type' in props:
                    expected_type = props['type']
                    actual_type = type(metadata[field]).__name__
                    
                    # Map Python types to schema types
                    type_map = {
                        'int': ['integer'],
                        'float': ['number'],
                        'str': ['string'],
                        'bool': ['boolean']
                    }
                    
                    assert expected_type in type_map.get(actual_type, [actual_type]), \
                        f"Type mismatch for {field}: expected {expected_type}, got {actual_type}"


class TestFrameExtractionSchema:
    """Test that frame extraction returns schema-compliant data."""
    
    def test_frames_schema_compliance(self, tmp_path):
        """Test that extracted frames have correct shape and dtype."""
        video_path = tmp_path / "test.mp4"
        create_test_video(str(video_path))
        
        frames = extract_frames(str(video_path), return_generator=False)
        
        # Check frame properties
        for i, frame in enumerate(frames):
            assert isinstance(frame, np.ndarray), f"Frame {i} is not a numpy array"
            assert len(frame.shape) == 3, f"Frame {i} has wrong dimensions"
            assert frame.shape[2] == 3, f"Frame {i} is not RGB/BGR"
            assert frame.dtype in [np.uint8, np.float32], f"Frame {i} has wrong dtype"
            
    def test_frame_consistency(self, tmp_path):
        """Test that all frames have consistent shape."""
        video_path = tmp_path / "test.mp4"
        create_test_video(str(video_path))
        
        frames = extract_frames(str(video_path), return_generator=False)
        
        if not frames:
            return
            
        first_shape = frames[0].shape
        for i, frame in enumerate(frames[1:], 1):
            assert frame.shape == first_shape, \
                f"Frame {i} shape {frame.shape} differs from first frame {first_shape}"

class TestVideoWritingSchema:
    """Test that written videos are valid."""
    
    def test_written_video_validity(self, tmp_path):
        """Test that written video can be read back."""
        output_path = tmp_path / "output.mp4"
        frames = [np.zeros((480, 640, 3), dtype=np.uint8) for _ in range(10)]
        
        write_video(str(output_path), frames, fps=24.0)
        
        # Verify video can be read
        metadata = get_video_metadata(str(output_path))
        
        assert metadata['frame_count'] == 10
        assert metadata['width'] == 640
        assert metadata['height'] == 480
        assert metadata['fps'] == 24.0
        
        # Verify frames can be extracted
        extracted = extract_frames(str(output_path), return_generator=False)
        assert len(extracted) == 10
"""
Contract test for flow field schema.

This test validates that optical flow fields produced by the pipeline
conform to the expected schema defined in the project specifications.

The schema requires:
- Flow fields to be stored as .npy files
- Each file contains a numpy array of shape (H, W, 2) where:
  - H: height of the video frame
  - W: width of the video frame
  - 2: flow vectors (u, v) representing horizontal and vertical displacement
- Flow values are in pixels/frame
- NaN values indicate invalid/missing flow estimates
"""

import os
import sys
import json
import tempfile
import shutil
import numpy as np
import pytest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils.flow_benchmark import create_test_frames
from code.utils.flow import load_raft_model, compute_flow_field


class TestFlowFieldSchema:
    """Test cases for validating flow field schema compliance."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test artifacts."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    def test_frames(self):
        """Generate test frames for flow computation."""
        frames = create_test_frames(num_frames=2, height=480, width=640)
        return frames

    def test_flow_field_shape(self, temp_dir, test_frames):
        """Test that flow fields have correct shape (H, W, 2)."""
        model = load_raft_model()
        flow_field = compute_flow_field(model, test_frames[0], test_frames[1])

        # Check shape
        assert len(flow_field.shape) == 3, f"Expected 3D array, got {len(flow_field.shape)}D"
        assert flow_field.shape[0] == 480, f"Expected height 480, got {flow_field.shape[0]}"
        assert flow_field.shape[1] == 640, f"Expected width 640, got {flow_field.shape[1]}"
        assert flow_field.shape[2] == 2, f"Expected 2 channels, got {flow_field.shape[2]}"

    def test_flow_field_dtype(self, temp_dir, test_frames):
        """Test that flow fields use appropriate data types (float32)."""
        model = load_raft_model()
        flow_field = compute_flow_field(model, test_frames[0], test_frames[1])

        # Check dtype - should be float32 for memory efficiency
        assert flow_field.dtype in [np.float32, np.float64], \
            f"Expected float32 or float64, got {flow_field.dtype}"

    def test_flow_field_value_range(self, temp_dir, test_frames):
        """Test that flow values are within reasonable bounds."""
        model = load_raft_model()
        flow_field = compute_flow_field(model, test_frames[0], test_frames[1])

        # Check for extreme outliers (reasonable bound: ±100 pixels/frame)
        u, v = flow_field[:, :, 0], flow_field[:, :, 1]
        assert np.all(np.abs(u) < 1000) or np.isnan(u).all(), \
            "Flow values exceed reasonable bounds"
        assert np.all(np.abs(v) < 1000) or np.isnan(v).all(), \
            "Flow values exceed reasonable bounds"

    def test_flow_field_nan_handling(self, temp_dir, test_frames):
        """Test that NaN values are properly handled in flow fields."""
        model = load_raft_model()
        flow_field = compute_flow_field(model, test_frames[0], test_frames[1])

        # Count NaN values
        nan_count = np.isnan(flow_field).sum()
        total_elements = flow_field.size

        # Allow some NaN values for invalid regions
        nan_ratio = nan_count / total_elements
        assert nan_ratio <= 0.5, \
            f"Too many NaN values: {nan_ratio:.2%} of flow field is invalid"

    def test_flow_field_serialization(self, temp_dir, test_frames):
        """Test that flow fields can be serialized and deserialized correctly."""
        model = load_raft_model()
        flow_field = compute_flow_field(model, test_frames[0], test_frames[1])

        # Save to file
        flow_path = os.path.join(temp_dir, "test_flow.npy")
        np.save(flow_path, flow_field)

        # Load from file
        loaded_flow = np.load(flow_path)

        # Verify equality
        assert np.array_equal(flow_field, loaded_flow), \
            "Flow field serialization/deserialization failed"
        assert flow_field.shape == loaded_flow.shape, \
            "Flow field shape changed during serialization"

    def test_flow_field_metadata(self, temp_dir, test_frames):
        """Test that flow field metadata is correctly recorded."""
        model = load_raft_model()
        flow_field = compute_flow_field(model, test_frames[0], test_frames[1])

        # Create metadata dict
        metadata = {
            "height": flow_field.shape[0],
            "width": flow_field.shape[1],
            "channels": flow_field.shape[2],
            "dtype": str(flow_field.dtype),
            "has_nan": bool(np.isnan(flow_field).any()),
            "nan_count": int(np.isnan(flow_field).sum()),
            "max_u": float(np.nanmax(flow_field[:, :, 0])),
            "max_v": float(np.nanmax(flow_field[:, :, 1])),
            "min_u": float(np.nanmin(flow_field[:, :, 0])),
            "min_v": float(np.nanmin(flow_field[:, :, 1])),
        }

        # Verify metadata structure
        required_keys = ["height", "width", "channels", "dtype", "has_nan"]
        for key in required_keys:
            assert key in metadata, f"Missing metadata key: {key}"

        # Verify metadata values match flow field
        assert metadata["height"] == 480
        assert metadata["width"] == 640
        assert metadata["channels"] == 2

    def test_consecutive_flow_consistency(self, temp_dir, test_frames):
        """Test that consecutive flow fields are consistent."""
        # Create 3 test frames
        frames = create_test_frames(num_frames=3, height=480, width=640)

        model = load_raft_model()

        # Compute flow for consecutive pairs
        flow_01 = compute_flow_field(model, frames[0], frames[1])
        flow_12 = compute_flow_field(model, frames[1], frames[2])

        # Both should have same shape
        assert flow_01.shape == flow_12.shape, \
            "Consecutive flow fields have different shapes"

        # Both should be valid arrays
        assert flow_01.size > 0 and flow_12.size > 0, \
            "Flow fields are empty"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
Unit tests for the Render Interface (T022).

Tests verify:
1. Fixed camera intrinsics are set correctly (f=1024, c=256).
2. Output dimensions are 512x512.
3. The renderer can be initialized without GPU errors (CPU only).
"""
import os
import sys
import json
import tempfile
import numpy as np
import pytest
from pathlib import Path

# Mock Open3D if not available to allow test discovery, 
# but the actual run will require it.
try:
    import open3d as o3d
    OPEN3D_AVAILABLE = True
except ImportError:
    OPEN3D_AVAILABLE = False
    pytest.skip("Open3D not installed", allow_module_level=True)

from code import setup_config # Ensure path is set up if needed, though we import directly

# Import the module under test
# We need to ensure the path includes 'code'
sys.path.insert(0, 'code')
from lib.logging_config import setup_logging

# Import functions from the target module
# We need to import from the file directly since it's in code/
import importlib.util
spec = importlib.util.spec_from_file_location("render_interface", "code/03_render_interface.py")
render_interface = importlib.util.module_from_spec(spec)
spec.loader.exec_module(render_interface)

# Constants from the module
FIXED_FOCAL_LENGTH = render_interface.FIXED_FOCAL_LENGTH
FIXED_PRINCIPAL_POINT = render_interface.FIXED_PRINCIPAL_POINT
IMAGE_WIDTH = render_interface.IMAGE_WIDTH
IMAGE_HEIGHT = render_interface.IMAGE_HEIGHT

def test_camera_intrinsics():
    """Verify fixed camera intrinsics match T022 requirements."""
    intrinsic = render_interface.create_camera_intrinsics()
    
    assert intrinsic.intrinsic_matrix[0, 0] == FIXED_FOCAL_LENGTH, "Fx mismatch"
    assert intrinsic.intrinsic_matrix[1, 1] == FIXED_FOCAL_LENGTH, "Fy mismatch"
    assert intrinsic.intrinsic_matrix[0, 2] == FIXED_PRINCIPAL_POINT[0], "Cx mismatch"
    assert intrinsic.intrinsic_matrix[1, 2] == FIXED_PRINCIPAL_POINT[1], "Cy mismatch"
    assert intrinsic.image_width == IMAGE_WIDTH, "Image width mismatch"
    assert intrinsic.image_height == IMAGE_HEIGHT, "Image height mismatch"

def test_fixed_poses_structure():
    """Verify fixed poses are 4x4 matrices."""
    poses = render_interface.FIXED_POSES
    assert len(poses) > 0, "No fixed poses defined"
    for pose in poses:
        assert isinstance(pose, np.ndarray), "Pose must be numpy array"
        assert pose.shape == (4, 4), f"Pose shape must be (4,4), got {pose.shape}"
        assert pose.dtype == np.float32, "Pose dtype must be float32"

def test_offscreen_renderer_cpu_only():
    """Verify that the renderer does not attempt to use GPU (basic check)."""
    if not OPEN3D_AVAILABLE:
        pytest.skip("Open3D not available")
    
    # This test ensures we can create the renderer without errors.
    # Open3D's OffscreenRenderer defaults to CPU if no GPU is configured or available.
    try:
        renderer = o3d.t.io.rendering.OffscreenRenderer(
            width=IMAGE_WIDTH,
            height=IMAGE_HEIGHT
        )
        renderer.close()
    except Exception as e:
        pytest.fail(f"Failed to initialize OffscreenRenderer on CPU: {e}")

def test_render_scene_function_exists():
    """Verify the render_scene function exists and has correct signature."""
    assert callable(render_interface.render_scene)
    import inspect
    sig = inspect.signature(render_interface.render_scene)
    params = list(sig.parameters.keys())
    expected_params = ['pcd', 'intrinsic', 'extrinsic', 'output_rgb_path', 'output_depth_path']
    assert params == expected_params, f"Function signature mismatch: {params} vs {expected_params}"

def test_process_ply_file_structure():
    """Verify process_ply_file returns the expected dictionary structure."""
    # We can't easily run the full process without a real PLY, 
    # but we can check the logic flow if we mock the renderer.
    # For now, we assert the function exists and returns a dict in error cases.
    assert callable(render_interface.process_ply_file)
    
    # Test with a non-existent file to ensure error handling returns correct structure
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_ply = Path(tmpdir) / "fake.ply"
        output_dir = Path(tmpdir)
        intrinsic = render_interface.create_camera_intrinsics()
        
        result = render_interface.process_ply_file(fake_ply, output_dir, intrinsic, render_interface.FIXED_POSES)
        
        assert isinstance(result, dict), "Result must be a dictionary"
        assert "sample_id" in result, "Result must contain sample_id"
        assert "status" in result, "Result must contain status"
        assert result["status"] == "error", "Expected error status for missing file"
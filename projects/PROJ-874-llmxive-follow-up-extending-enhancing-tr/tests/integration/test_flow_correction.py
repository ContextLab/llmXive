import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import numpy as np
import pytest

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import Config, get_config, get_results_dir, get_raw_dir
from correct import (
    get_naive_baseline_paths,
    verify_naive_baselines_exist,
    verify_flow_fields_exist,
    process_video_flow,
    get_flow_field_paths
)
from utils.video import write_video, extract_frames

@pytest.fixture
def temp_config():
    """Create a temporary config and directory structure for testing."""
    temp_dir = tempfile.mkdtemp()
    config_data = {
        "seed": 42,
        "dataset_paths": {
            "narrlv": os.path.join(temp_dir, "data", "raw", "narrlv"),
            "vbench": os.path.join(temp_dir, "data", "raw", "vbench")
        },
        "results_dir": os.path.join(temp_dir, "data", "results"),
        "raw_dir": os.path.join(temp_dir, "data", "raw"),
        "processed_dir": os.path.join(temp_dir, "data", "processed"),
        "flow_model": "raft-small",
        "flow_precision": "fp32"
    }
    
    config_file = os.path.join(temp_dir, "config.json")
    with open(config_file, 'w') as f:
        json.dump(config_data, f)
    
    yield config_file, temp_dir
    
    shutil.rmtree(temp_dir)

def create_test_video(path, num_frames=10, height=64, width=64):
    """Create a dummy video file for testing."""
    frames = [np.random.randint(0, 255, (height, width, 3), dtype=np.uint8) for _ in range(num_frames)]
    write_video(frames, path, fps=24)

def create_test_flow(path, num_frames=10, height=64, width=64):
    """Create a dummy flow field JSON file for testing."""
    flow_data = []
    for i in range(num_frames):
        flow = np.random.randn(height, width, 2).astype(np.float32)
        flow_data.append({
            "frame_idx": i,
            "flow": flow.tolist()
        })
    
    with open(path, 'w') as f:
        json.dump(flow_data, f)

def test_verify_naive_baselines_exist_success(temp_config):
    config_file, temp_dir = temp_config
    config = get_config(config_file)
    
    # Create naive baseline directory
    naive_dir = get_raw_dir(config) / "naive_baseline"
    naive_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test videos
    create_test_video(naive_dir / "test1.mp4")
    create_test_video(naive_dir / "test2.mp4")
    
    assert verify_naive_baselines_exist(config) is True

def test_verify_naive_baselines_exist_failure(temp_config):
    config_file, temp_dir = temp_config
    config = get_config(config_file)
    
    # Ensure directory doesn't exist or is empty
    naive_dir = get_raw_dir(config) / "naive_baseline"
    if naive_dir.exists():
        shutil.rmtree(naive_dir)
    
    with pytest.raises(Exception): # Should raise or return False depending on impl
        # In current impl, it raises DatasetNotFoundError via get_naive_baseline_paths
        verify_naive_baselines_exist(config)

def test_verify_flow_fields_exist_success(temp_config):
    config_file, temp_dir = temp_config
    config = get_config(config_file)
    
    # Setup naive baselines
    naive_dir = get_raw_dir(config) / "naive_baseline"
    naive_dir.mkdir(parents=True, exist_ok=True)
    create_test_video(naive_dir / "test1.mp4")
    
    # Setup flow fields
    results_dir = get_results_dir(config)
    flow_dir = results_dir / "flow_fields"
    flow_dir.mkdir(parents=True, exist_ok=True)
    create_test_flow(flow_dir / "test1.json")
    
    flow_map = verify_flow_fields_exist(config)
    assert "test1" in flow_map

def test_verify_flow_fields_exist_failure(temp_config):
    config_file, temp_dir = temp_config
    config = get_config(config_file)
    
    # Setup naive baselines
    naive_dir = get_raw_dir(config) / "naive_baseline"
    naive_dir.mkdir(parents=True, exist_ok=True)
    create_test_video(naive_dir / "test1.mp4")
    
    # Setup flow fields (missing test1)
    results_dir = get_results_dir(config)
    flow_dir = results_dir / "flow_fields"
    flow_dir.mkdir(parents=True, exist_ok=True)
    create_test_flow(flow_dir / "test2.json") # Different ID
    
    with pytest.raises(Exception):
        verify_flow_fields_exist(config)

def test_process_video_flow(temp_config):
    config_file, temp_dir = temp_config
    config = get_config(config_file)
    
    # Setup naive baselines
    naive_dir = get_raw_dir(config) / "naive_baseline"
    naive_dir.mkdir(parents=True, exist_ok=True)
    video_path = naive_dir / "test1.mp4"
    create_test_video(video_path, num_frames=5)
    
    # Setup flow fields
    results_dir = get_results_dir(config)
    flow_dir = results_dir / "flow_fields"
    flow_dir.mkdir(parents=True, exist_ok=True)
    flow_path = flow_dir / "test1.json"
    create_test_flow(flow_path, num_frames=5)
    
    # Output dir
    output_dir = results_dir / "condition_c"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run processing
    output_path = process_video_flow(config, video_path, flow_path, output_dir)
    
    assert output_path.exists()
    
    # Verify output video has frames
    frames = extract_frames(output_path)
    assert len(frames) == 5
    assert frames[0].shape == (64, 64, 3)

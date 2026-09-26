import os
import sys
import json
import tempfile
import numpy as np
import pytest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scripts.verify_alignment import calculate_iou, verify_spatial_alignment, load_modalities_from_disk

@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "modalities"
        data_dir.mkdir()
        
        # Create dummy modalities
        # Grid: 10x10 binary
        grid = np.zeros((10, 10), dtype=np.uint8)
        grid[3:7, 3:7] = 1
        np.save(data_dir / "occupancy_grid.npy", grid)
        
        # Depth: 10x10 with values
        depth = np.zeros((10, 10), dtype=np.float32)
        depth[3:7, 3:7] = 1.0
        np.save(data_dir / "depth_frame.npy", depth)
        
        # RGB: 10x10x3
        rgb = np.zeros((10, 10, 3), dtype=np.uint8)
        rgb[3:7, 3:7, :] = 255
        np.save(data_dir / "rgb_frame.npy", rgb)
        
        yield data_dir

@pytest.fixture
def temp_calib_report():
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "calibration_report.json"
        calib_data = {
            "extrinsic": np.eye(4).tolist(),
            "intrinsic": np.eye(3).tolist(),
            "status": "valid"
        }
        with open(report_path, 'w') as f:
            json.dump(calib_data, f)
        yield report_path

def test_calculate_iou_perfect_overlap():
    grid1 = np.ones((10, 10), dtype=np.uint8)
    grid2 = np.ones((10, 10), dtype=np.uint8)
    assert calculate_iou(grid1, grid2) == 1.0

def test_calculate_iou_no_overlap():
    grid1 = np.zeros((10, 10), dtype=np.uint8)
    grid2 = np.ones((10, 10), dtype=np.uint8)
    assert calculate_iou(grid1, grid2) == 0.0

def test_calculate_iou_partial_overlap():
    grid1 = np.zeros((10, 10), dtype=np.uint8)
    grid1[0:5, 0:5] = 1
    grid2 = np.zeros((10, 10), dtype=np.uint8)
    grid2[2:7, 2:7] = 1
    
    # Intersection: 3x3 = 9
    # Union: 25 + 25 - 9 = 41
    iou = calculate_iou(grid1, grid2)
    assert abs(iou - 9/41) < 0.001

def test_load_modalities_from_disk(temp_data_dir):
    modalities = load_modalities_from_disk(temp_data_dir)
    assert 'rgb' in modalities
    assert 'depth' in modalities
    assert 'grid' in modalities
    assert modalities['grid'].shape == (10, 10)

def test_verify_spatial_alignment(temp_data_dir, temp_calib_report):
    modalities = load_modalities_from_disk(temp_data_dir)
    report = verify_spatial_alignment(modalities, temp_calib_report, iou_threshold=0.9)
    
    assert report['status'] == 'success'
    assert report['passed'] is True
    assert 'iou_scores' in report
    assert 'depth_vs_grid' in report['iou_scores']
    assert 'rgb_edges_vs_depth_edges' in report['iou_scores']
    
    # In our dummy data, depth and grid are perfectly aligned
    assert report['iou_scores']['depth_vs_grid'] == 1.0
    # RGB edges and depth edges should also align in this dummy case
    assert report['iou_scores']['rgb_edges_vs_depth_edges'] == 1.0

def test_verify_spatial_alignment_failure(temp_data_dir, temp_calib_report):
    # Modify grid to be misaligned
    grid = np.zeros((10, 10), dtype=np.uint8)
    grid[0:4, 0:4] = 1 # Misaligned with depth which is at 3:7
    np.save(temp_data_dir / "occupancy_grid.npy", grid)
    
    modalities = load_modalities_from_disk(temp_data_dir)
    report = verify_spatial_alignment(modalities, temp_calib_report, iou_threshold=0.9)
    
    assert report['passed'] is False
    assert report['status'] == 'failed'
    assert report['iou_scores']['depth_vs_grid'] < 0.9

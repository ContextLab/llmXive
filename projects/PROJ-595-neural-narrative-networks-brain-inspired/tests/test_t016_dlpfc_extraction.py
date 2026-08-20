"""
Tests for T016: DLPFC BOLD timecourse extraction.

These tests verify that:
1. The extraction script runs without error
2. Output file is created and valid
3. Timecourses are non-empty and properly shaped
4. Error handling works for missing masks (E001) and empty data (E002)
"""
import os
import json
import tempfile
import shutil
import numpy as np
import nibabel as nib
from pathlib import Path
import pytest

# Add code directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from utils.logging_config import get_logger
from config import get_config

logger = get_logger(__name__)

@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory structure for testing."""
    temp_dir = tempfile.mkdtemp()
    base = Path(temp_dir)
    
    # Create directory structure
    (base / 'raw' / 'ds001495').mkdir(parents=True)
    (base / 'processed').mkdir(parents=True)
    
    # Create a mock subject with functional data
    sub_dir = base / 'raw' / 'ds001495' / 'sub-01' / 'func'
    sub_dir.mkdir(parents=True)
    
    # Create a mock 4D functional image (10x10x10 voxels, 100 timepoints)
    func_data = np.random.randn(10, 10, 10, 100).astype(np.float32)
    func_img = nib.Nifti1Image(func_data, np.eye(4))
    func_path = sub_dir / 'sub-01_task-story_bold.nii.gz'
    nib.save(func_img, func_path)
    
    # Create a mock DLPFC mask (small region in the center)
    mask_data = np.zeros((10, 10, 10), dtype=np.float32)
    mask_data[4:7, 4:7, 4:7] = 1.0  # 3x3x3 cube
    mask_img = nib.Nifti1Image(mask_data, np.eye(4))
    mask_path = base / 'processed' / 'mask_dlpfc.nii.gz'
    nib.save(mask_img, mask_path)
    
    # Create mask_paths.json
    mask_paths = {
        'dlpfc': str(mask_path),
        'left_hippocampus': str(mask_path),
        'right_hippocampus': str(mask_path)
    }
    mask_json_path = base / 'processed' / 'mask_paths.json'
    with open(mask_json_path, 'w') as f:
        json.dump(mask_paths, f)
    
    yield base
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_mask_loading(temp_data_dir):
    """Test that masks are loaded correctly from mask_paths.json."""
    from code_04_extract_roi_timecourses import load_mask_from_json
    
    mask_json = str(temp_data_dir / 'processed' / 'mask_paths.json')
    mask_data = load_mask_from_json(mask_json, 'dlpfc')
    
    assert mask_data is not None
    assert mask_data.shape == (10, 10, 10)
    assert np.sum(mask_data > 0) == 27  # 3x3x3 cube

def test_extraction_script_creates_output(temp_data_dir):
    """Test that the main script creates the output file."""
    import subprocess
    
    # Set up environment
    env = os.environ.copy()
    env['DATA_DIR'] = str(temp_data_dir)
    
    # Run the extraction script
    result = subprocess.run(
        ['python', 'code/04_extract_roi_timecourses.py'],
        env=env,
        capture_output=True,
        text=True,
        cwd=str(temp_data_dir.parent.parent)
    )
    
    # Check that output file was created
    output_path = temp_data_dir / 'processed' / 'roi_dlpfc.npy'
    assert output_path.exists(), f"Output file not created: {output_path}"
    
    # Verify output content
    data = np.load(str(output_path))
    assert data.size > 0, "Output file is empty"
    assert data.shape[0] > 0, "No subjects extracted"

def test_empty_mask_raises_error(temp_data_dir):
    """Test that an empty mask triggers E002 error."""
    from code_04_extract_roi_timecourses import extract_roi_timecourse
    
    # Create empty mask
    empty_mask = np.zeros((10, 10, 10), dtype=np.float32)
    
    # Create mock functional image
    func_data = np.random.randn(10, 10, 10, 100).astype(np.float32)
    func_img = nib.Nifti1Image(func_data, np.eye(4))
    
    with pytest.raises(ValueError, match="no valid voxels"):
        extract_roi_timecourse(
            func_img,
            empty_mask,
            np.eye(4),
            np.eye(4)
        )

def test_missing_mask_json_raises_error(temp_data_dir):
    """Test that missing mask_paths.json triggers E001 error."""
    from code_04_extract_roi_timecourses import load_mask_from_json
    
    with pytest.raises(FileNotFoundError, match="mask_paths.json"):
        load_mask_from_json('/nonexistent/path.json', 'dlpfc')

def test_roi_not_in_json_raises_error(temp_data_dir):
    """Test that missing ROI in JSON triggers KeyError."""
    from code_04_extract_roi_timecourses import load_mask_from_json
    
    mask_json = str(temp_data_dir / 'processed' / 'mask_paths.json')
    
    with pytest.raises(KeyError, match="ROI.*not found"):
        load_mask_from_json(mask_json, 'nonexistent_roi')

def test_output_shape_validation(temp_data_dir):
    """Test that output has correct shape and data types."""
    import subprocess
    
    env = os.environ.copy()
    env['DATA_DIR'] = str(temp_data_dir)
    
    subprocess.run(
        ['python', 'code/04_extract_roi_timecourses.py'],
        env=env,
        capture_output=True,
        cwd=str(temp_data_dir.parent.parent)
    )
    
    output_path = temp_data_dir / 'processed' / 'roi_dlpfc.npy'
    data = np.load(str(output_path))
    
    # Should be 2D: (subjects, timepoints)
    assert len(data.shape) == 2, f"Expected 2D array, got {len(data.shape)}D"
    assert data.shape[0] >= 1, "At least one subject should be processed"
    assert data.shape[1] >= 1, "At least one timepoint should be extracted"
    assert data.dtype in [np.float32, np.float64], f"Unexpected dtype: {data.dtype}"
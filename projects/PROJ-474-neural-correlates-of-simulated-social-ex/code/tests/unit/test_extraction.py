"""
Unit tests for ROI Time-Series Extraction (T024).

Tests verify:
1. Atlas loading and ROI mapping.
2. Correct extraction of time-series from synthetic NIfTI data.
3. Handling of missing ROIs.
"""
import pytest
import numpy as np
import nibabel as nib
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import json

# Mock nilearn to avoid heavy atlas downloads in unit tests
# We simulate the atlas structure instead
@pytest.fixture
def mock_atlas_data():
    """Creates a mock atlas image and label mapping."""
    # Create a 3D volume (10x10x10)
    data = np.zeros((10, 10, 10), dtype=np.int32)
    
    # Define dummy ROIs
    # Index 1: PCC (voxels at 2,2,2 to 3,3,3)
    data[2:4, 2:4, 2:4] = 1
    # Index 2: mPFC (voxels at 6,6,6 to 7,7,7)
    data[6:8, 6:8, 6:8] = 2
    # Index 3: Angular (voxels at 1,5,5)
    data[1, 5, 5] = 3
    
    # Create NIfTI image
    affine = np.eye(4)
    img = nib.Nifti1Image(data, affine)
    
    labels = [
        "Background",  # Index 0
        "Posterior Cingulate Cortex", # Index 1
        "Medial Prefrontal Cortex",   # Index 2
        "Angular Gyrus"               # Index 3
    ]
    
    return img, labels

@pytest.fixture
def mock_subject_data():
    """Creates a mock subject preprocessed NIfTI with known time-series."""
    # 4D volume: 10x10x10 spatial, 5 timepoints
    data = np.zeros((10, 10, 10, 5), dtype=np.float32)
    
    # Set specific values for PCC region (index 1)
    # PCC voxels: 2:4, 2:4, 2:4
    data[2:4, 2:4, 2:4, :] = 10.0  # Constant 10.0
    
    # Set specific values for mPFC region (index 2)
    # mPFC voxels: 6:8, 6:8, 6:8
    data[6:8, 6:8, 6:8, :] = 20.0  # Constant 20.0
    
    # Set specific values for Angular region (index 3)
    # Angular voxel: 1, 5, 5
    data[1, 5, 5, :] = 30.0  # Constant 30.0
    
    affine = np.eye(4)
    img = nib.Nifti1Image(data, affine)
    return img

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_atlas_harvard_oxford(mock_atlas_data):
    """Test that we can construct a name-to-index map."""
    atlas_img, labels = mock_atlas_data
    
    # Simulate the logic from extraction.py
    name_to_idx = {name: idx for idx, name in enumerate(labels) if idx > 0}
    
    assert "Posterior Cingulate Cortex" in name_to_idx
    assert name_to_idx["Posterior Cingulate Cortex"] == 1
    assert name_to_idx["Medial Prefrontal Cortex"] == 2
    assert name_to_idx["Angular Gyrus"] == 3

def test_extract_roi_timeseries(mock_atlas_data, mock_subject_data, temp_dir):
    """Test extraction of time-series from a mock subject."""
    from src.extraction import extract_roi_timeseries
    
    atlas_img, labels = mock_atlas_data
    name_to_idx = {name: idx for idx, name in enumerate(labels) if idx > 0}
    
    # Save mock subject to temp file
    subj_path = temp_dir / "test_subject.nii.gz"
    nib.save(mock_subject_data, str(subj_path))
    
    # Extract
    results = extract_roi_timeseries(
        subject_preprocessed_path=subj_path,
        atlas_img=atlas_img,
        name_to_idx=name_to_idx,
        rois=["PCC", "mPFC", "Angular"]
    )
    
    # Verify PCC (should be mean of 10.0s)
    assert "PCC" in results
    assert results["PCC"] is not None
    assert np.allclose(results["PCC"], 10.0)
    
    # Verify mPFC
    assert "mPFC" in results
    assert results["mPFC"] is not None
    assert np.allclose(results["mPFC"], 20.0)
    
    # Verify Angular
    assert "Angular" in results
    assert results["Angular"] is not None
    assert np.allclose(results["Angular"], 30.0)

def test_extract_missing_roi(mock_atlas_data, mock_subject_data, temp_dir):
    """Test behavior when an ROI is not found in the atlas."""
    from src.extraction import extract_roi_timeseries
    
    atlas_img, labels = mock_atlas_data
    name_to_idx = {name: idx for idx, name in enumerate(labels) if idx > 0}
    
    subj_path = temp_dir / "test_subject.nii.gz"
    nib.save(mock_subject_data, str(subj_path))
    
    # Request a non-existent ROI
    results = extract_roi_timeseries(
        subject_preprocessed_path=subj_path,
        atlas_img=atlas_img,
        name_to_idx=name_to_idx,
        rois=["NonExistentROI"]
    )
    
    assert "NonExistentROI" in results
    assert results["NonExistentROI"] is None

def test_process_subject_extraction_integration(temp_dir, mock_atlas_data, mock_subject_data, monkeypatch):
    """Integration test for process_subject_extraction."""
    from src.extraction import process_subject_extraction
    
    # Setup mock config
    config = {
        "paths": {
            "data_dir": str(temp_dir / "data"),
            "processed_dir": str(temp_dir / "processed"),
            "results_dir": str(temp_dir / "results")
        },
        "atlas": {
            "type": "harvard_oxford"
        }
    }
    
    # Create directories
    (temp_dir / "processed").mkdir(parents=True)
    (temp_dir / "results").mkdir(parents=True)
    
    # Save mock subject as preprocessed file
    subj_path = temp_dir / "processed" / "preprocessed_sub-01.nii.gz"
    nib.save(mock_subject_data, str(subj_path))
    
    # Mock the atlas loading to return our mock data
    def mock_load_atlas(atlas_type):
        return mock_atlas_data[0], {name: idx for idx, name in enumerate(mock_atlas_data[1]) if idx > 0}
    
    with patch('src.extraction.load_atlas', side_effect=mock_load_atlas):
        result = process_subject_extraction(
            subject_id="sub-01",
            config=config,
            qc_list_path=temp_dir / "qc.json" # Dummy path
        )
    
    assert result["status"] == "success"
    assert result["subject_id"] == "sub-01"
    
    # Check output file
    output_file = Path(result["output_file"])
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        data = json.load(f)
    
    assert data["subject_id"] == "sub-01"
    assert "roi_timeseries" in data
    assert len(data["roi_timeseries"]["PCC"]) == 5 # 5 timepoints
    assert np.allclose(data["roi_timeseries"]["PCC"], 10.0)
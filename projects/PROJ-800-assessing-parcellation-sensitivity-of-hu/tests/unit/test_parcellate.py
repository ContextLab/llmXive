"""
Unit tests for the parcellation module.

Tests cover:
- Atlas mask loading
- fMRI data loading
- Time series extraction (chunked)
- Adjacency matrix computation
- End-to-end pipeline
"""

import os
import tempfile
import numpy as np
import nibabel as nib
import pytest
from pathlib import Path

from code.parcellate import (
    load_atlas_mask,
    load_fMRI_data,
    extract_timeseries_chunked,
    compute_adjacency_matrix,
    extract_and_parcellate
)
from code.utils.logger import ProcessingError


@pytest.fixture
def temp_atlas():
    """Create a temporary 3D atlas mask."""
    with tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False) as f:
        # Create a simple 3x3x3 atlas with 2 regions
        atlas_data = np.zeros((3, 3, 3), dtype=np.int32)
        atlas_data[0, :, :] = 1  # Region 1
        atlas_data[1, :, :] = 2  # Region 2
        atlas_data[2, :, :] = 0  # Background
        
        img = nib.Nifti1Image(atlas_data, np.eye(4))
        nib.save(img, f.name)
        
        yield f.name
        os.unlink(f.name)

@pytest.fixture
def temp_fmri():
    """Create a temporary 4D fMRI dataset."""
    with tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False) as f:
        # Create 4D data: 3x3x3 spatial, 10 time points
        n_timepoints = 10
        fmri_data = np.random.randn(3, 3, 3, n_timepoints).astype(np.float32)
        
        img = nib.Nifti1Image(fmri_data, np.eye(4))
        nib.save(img, f.name)
        
        yield f.name
        os.unlink(f.name)

@pytest.fixture
def temp_output():
    """Create a temporary output path."""
    with tempfile.NamedTemporaryFile(suffix='.npz', delete=False) as f:
        yield f.name
        if os.path.exists(f.name):
            os.unlink(f.name)

def test_load_atlas_mask(temp_atlas):
    """Test loading an atlas mask."""
    mask = load_atlas_mask(temp_atlas)
    assert mask.shape == (3, 3, 3)
    assert mask.dtype in [np.int32, np.int64, np.float32, np.float64]
    assert np.unique(mask).tolist() == [0, 1, 2]

def test_load_atlas_mask_not_found():
    """Test loading a non-existent atlas."""
    with pytest.raises(ProcessingError):
        load_atlas_mask('/nonexistent/path.nii.gz')

def test_load_fMRI_data(temp_fmri):
    """Test loading fMRI data."""
    data, shape = load_fMRI_data(temp_fmri)
    assert data.shape == (3, 3, 3, 10)
    assert len(shape) == 4

def test_load_fMRI_data_not_found():
    """Test loading a non-existent fMRI file."""
    with pytest.raises(ProcessingError):
        load_fMRI_data('/nonexistent/path.nii.gz')

def test_extract_timeseries_chunked(temp_fmri, temp_atlas):
    """Test chunked time series extraction."""
    mask = load_atlas_mask(temp_atlas)
    time_series, labels = extract_timeseries_chunked(
        temp_fmri,
        mask,
        chunk_size=5,
        min_voxel_count=1
    )
    
    # Should have 2 regions (labels 1 and 2)
    assert time_series.shape[0] == 2
    assert time_series.shape[1] == 10
    assert len(labels) == 2
    assert 1 in labels and 2 in labels

def test_extract_timeseries_with_threshold(temp_fmri, temp_atlas):
    """Test time series extraction with minimum voxel count."""
    mask = load_atlas_mask(temp_atlas)
    time_series, labels = extract_timeseries_chunked(
        temp_fmri,
        mask,
        chunk_size=5,
        min_voxel_count=10  # Higher than any region has
    )
    
    # All regions should be filtered out
    assert time_series.shape[0] == 0
    assert len(labels) == 0

def test_compute_adjacency_matrix_pearson():
    """Test Pearson correlation adjacency matrix."""
    n_regions = 5
    n_timepoints = 100
    time_series = np.random.randn(n_regions, n_timepoints)
    labels = np.arange(1, n_regions + 1)
    
    adj_matrix, result_labels = compute_adjacency_matrix(
        time_series,
        labels,
        method='pearson',
        threshold=0.0
    )
    
    assert adj_matrix.shape == (n_regions, n_regions)
    assert np.allclose(np.diag(adj_matrix), 1.0)  # Self-correlation is 1
    assert len(result_labels) == n_regions

def test_compute_adjacency_matrix_threshold():
    """Test adjacency matrix with threshold."""
    n_regions = 5
    n_timepoints = 100
    time_series = np.random.randn(n_regions, n_timepoints)
    labels = np.arange(1, n_regions + 1)
    
    # Apply high threshold
    adj_matrix, _ = compute_adjacency_matrix(
        time_series,
        labels,
        method='pearson',
        threshold=0.99  # Very high threshold
    )
    
    # Most edges should be zero
    non_zero = np.sum(adj_matrix != 0)
    assert non_zero <= n_regions  # Only diagonal guaranteed

def test_extract_and_parcellate(temp_fmri, temp_atlas, temp_output):
    """Test end-to-end parcellation pipeline."""
    metadata = extract_and_parcellate(
        fmri_path=temp_fmri,
        atlas_path=temp_atlas,
        output_path=temp_output,
        chunk_size=5,
        correlation_method='pearson',
        threshold=0.0,
        min_voxel_count=1
    )
    
    assert metadata['n_regions'] == 2
    assert metadata['n_timepoints'] == 10
    assert os.path.exists(metadata['output_path'])
    assert os.path.exists(metadata['labels_path'])

def test_extract_and_parcellate_invalid_shape(temp_atlas):
    """Test parcellation with mismatched shapes."""
    with tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False) as f:
        # Create fMRI with wrong spatial dimensions
        fmri_data = np.random.randn(5, 5, 5, 10).astype(np.float32)
        img = nib.Nifti1Image(fmri_data, np.eye(4))
        nib.save(img, f.name)
        
        with tempfile.NamedTemporaryFile(suffix='.npz', delete=False) as out_f:
            with pytest.raises(ProcessingError):
                extract_and_parcellate(
                    fmri_path=f.name,
                    atlas_path=temp_atlas,
                    output_path=out_f.name
                )
            
            os.unlink(out_f.name)
        os.unlink(f.name)

def test_compute_adjacency_matrix_spearman():
    """Test Spearman correlation adjacency matrix."""
    n_regions = 5
    n_timepoints = 100
    time_series = np.random.randn(n_regions, n_timepoints)
    labels = np.arange(1, n_regions + 1)
    
    adj_matrix, _ = compute_adjacency_matrix(
        time_series,
        labels,
        method='spearman',
        threshold=0.0
    )
    
    assert adj_matrix.shape == (n_regions, n_regions)
    assert np.allclose(np.diag(adj_matrix), 1.0)

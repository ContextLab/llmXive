"""
Unit tests for the overlap.py module.
"""
import os
import numpy as np
import pytest
from pathlib import Path
import tempfile
import nibabel as nib

from overlap import (
    create_strict_containment_map,
    generate_schaefer_to_aal_mapping
)
from utils.logger import ProcessingError


def test_create_strict_containment_map_basic():
    """Test basic majority vote mapping."""
    # Create a simple 10x10x10 mask
    high_res_mask = np.zeros((10, 10, 10), dtype=np.int32)
    low_res_mask = np.zeros((10, 10, 10), dtype=np.int32)
    
    # High-res node 1 occupies voxels 0-4 in x, 0-9 in y, 0-9 in z
    high_res_mask[0:5, :, :] = 1
    
    # Low-res node 2 occupies voxels 0-4 in x (same as high-res)
    low_res_mask[0:5, :, :] = 2
    # Low-res node 3 occupies voxels 5-9 in x
    low_res_mask[5:10, :, :] = 3
    
    result = create_strict_containment_map(
        high_res_mask,
        low_res_mask,
        high_res_label=1,
        low_res_labels=[2, 3]
    )
    
    assert 1 in result
    assert result[1] == 2


def test_create_strict_containment_map_mixed():
    """Test majority vote with mixed overlap."""
    high_res_mask = np.zeros((10, 10, 10), dtype=np.int32)
    low_res_mask = np.zeros((10, 10, 10), dtype=np.int32)
    
    # High-res node 1: 60 voxels in low-res node 1, 40 voxels in low-res node 2
    high_res_mask[0:6, :, :] = 1  # 6*10*10 = 600 voxels
    low_res_mask[0:4, :, :] = 1   # 4*10*10 = 400 voxels overlap
    low_res_mask[4:6, :, :] = 2   # 2*10*10 = 200 voxels overlap
    
    # Actually, let's do a more precise test
    high_res_mask = np.zeros((10, 10, 10), dtype=np.int32)
    low_res_mask = np.zeros((10, 10, 10), dtype=np.int32)
    
    # High-res node 1: 100 voxels total
    high_res_mask[0:10, 0:10, 0:1] = 1  # 100 voxels
    
    # Low-res: 60 voxels of node 1, 40 voxels of node 2
    low_res_mask[0:6, 0:10, 0:1] = 1
    low_res_mask[6:10, 0:10, 0:1] = 2
    
    result = create_strict_containment_map(
        high_res_mask,
        low_res_mask,
        high_res_label=1,
        low_res_labels=[1, 2]
    )
    
    assert result[1] == 1  # Majority is node 1


def test_create_strict_containment_map_no_overlap():
    """Test when there is no overlap."""
    high_res_mask = np.zeros((10, 10, 10), dtype=np.int32)
    low_res_mask = np.zeros((10, 10, 10), dtype=np.int32)
    
    high_res_mask[0:5, :, :] = 1
    low_res_mask[5:10, :, :] = 2  # No overlap
    
    result = create_strict_containment_map(
        high_res_mask,
        low_res_mask,
        high_res_label=1,
        low_res_labels=[2]
    )
    
    assert result == {}


def test_generate_schaefer_to_aal_mapping():
    """Test the full mapping generation."""
    # Create small synthetic masks
    shape = (10, 10, 10)
    schaefer_mask = np.zeros(shape, dtype=np.int32)
    aal_mask = np.zeros(shape, dtype=np.int32)
    
    # Schaefer nodes: 1, 2, 3
    schaefer_mask[0:3, :, :] = 1
    schaefer_mask[3:6, :, :] = 2
    schaefer_mask[6:9, :, :] = 3
    
    # AAL nodes: 10, 20
    aal_mask[0:5, :, :] = 10
    aal_mask[5:10, :, :] = 20
    
    schaefer_labels = [1, 2, 3]
    aal_labels = [10, 20]
    
    mapping = generate_schaefer_to_aal_mapping(
        schaefer_labels,
        aal_labels,
        schaefer_mask,
        aal_mask
    )
    
    # Check shape
    assert mapping.shape[0] == max(schaefer_labels) + 1
    
    # Check mappings
    # Node 1 (0-2) -> AAL 10 (0-4)
    assert mapping[1] == 10
    # Node 2 (3-5) -> AAL 10 (0-4) overlaps 3-4, AAL 20 (5-9) overlaps 5
    # Majority: 2 voxels in AAL 10, 1 voxel in AAL 20 -> 10
    assert mapping[2] == 10
    # Node 3 (6-8) -> AAL 20 (5-9)
    assert mapping[3] == 20
    
    # Check background is -1
    assert mapping[0] == -1
    assert mapping[4] == -1
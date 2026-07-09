"""
Data loading utilities for HCP OpenNeuro dMRI and fMRI data.

This module handles the retrieval and basic parsing of HCP data.
It supports fetching data from the OpenNeuro repository or loading
from local cached directories.
"""
import os
import tempfile
import shutil
from pathlib import Path
import json
from typing import Optional, Tuple, Dict, Any, Union
import numpy as np
import nibabel as nib
import pandas as pd

# Constants for HCP OpenNeuro dataset
# Using a specific HCP 1200 Subjects release dataset on OpenNeuro
HCP_OPENNEURO_URL = "https://openneuro.org/datasets/ds000224/versions/1.0.0"
# Local cache directory relative to project root
LOCAL_CACHE_DIR = "data/raw/hcp_cache"

def _ensure_cache_dir() -> Path:
    """Ensure the local cache directory exists."""
    cache_path = Path(LOCAL_CACHE_DIR)
    cache_path.mkdir(parents=True, exist_ok=True)
    return cache_path

def _download_subject_data(subject_id: str, modality: str) -> Path:
    """
    Download subject data from OpenNeuro.
    
    Note: In a real production environment, this would use the datalad 
    or awscli tools to fetch specific files. For this implementation,
    we simulate the download structure or check for local existence.
    Since we cannot guarantee network access in all environments, 
    this function attempts to locate existing data or raises a clear error
    if data is missing, rather than fabricating it.
    
    Args:
        subject_id: HCP subject ID (e.g., '100307')
        modality: 'dmri' or 'fmri'
        
    Returns:
        Path to the subject's data directory
    """
    cache_root = _ensure_cache_dir()
    subject_dir = cache_root / subject_id / modality
    
    if subject_dir.exists():
        return subject_dir
    
    # In a real pipeline, we would trigger a download here.
    # For this task, we verify if a placeholder structure exists or fail.
    # We do not fabricate data.
    raise FileNotFoundError(
        f"HCP data for subject {subject_id} ({modality}) not found in {cache_root}. "
        f"Please ensure data is downloaded from OpenNeuro (ds000224) or the appropriate HCP source. "
        f"Expected path: {subject_dir}"
    )

def load_hcp_dmri(subject_id: str) -> Dict[str, Any]:
    """
    Load diffusion MRI data for a specific HCP subject.
    
    Args:
        subject_id: HCP subject ID (e.g., '100307')
        
    Returns:
        Dictionary containing:
            - 'nifti': Nibabel image object
            - 'bval': Path to b-values file
            - 'bvec': Path to b-vectors file
            - 'subject_id': The subject ID string
    """
    data_path = _download_subject_data(subject_id, "dmri")
    
    # Expected file patterns (HCP standard)
    nifti_path = data_path / f"{subject_id}_dwi.nii.gz"
    bval_path = data_path / f"{subject_id}_dwi.bval"
    bvec_path = data_path / f"{subject_id}_dwi.bvec"
    
    if not nifti_path.exists():
        # Fallback to generic naming if subject-specific fails
        nifti_path = list(data_path.glob("*dwi.nii.gz"))
        if nifti_path:
            nifti_path = nifti_path[0]
        else:
            raise FileNotFoundError(f"No DWI nifti file found for {subject_id}")
    
    img = nib.load(nifti_path)
    
    bval_data = None
    bvec_data = None
    
    if bval_path.exists():
        bval_data = np.loadtxt(bval_path)
    else:
        # Try to find any .bval file
        bvals = list(data_path.glob("*.bval"))
        if bvals:
            bval_data = np.loadtxt(bvals[0])
        
    if bvec_path.exists():
        bvec_data = np.loadtxt(bvec_path)
    else:
        # Try to find any .bvec file
        bvecs = list(data_path.glob("*.bvec"))
        if bvecs:
            bvec_data = np.loadtxt(bvecs[0])

    return {
        "nifti": img,
        "bval": bval_data,
        "bvec": bvec_data,
        "subject_id": subject_id,
        "affine": img.affine,
        "shape": img.shape
    }

def load_hcp_fmri(subject_id: str) -> Dict[str, Any]:
    """
    Load functional MRI data for a specific HCP subject.
    
    Args:
        subject_id: HCP subject ID (e.g., '100307')
        
    Returns:
        Dictionary containing:
            - 'nifti': Nibabel image object (4D)
            - 'json': Metadata dictionary (if available)
            - 'subject_id': The subject ID string
            - 'repetition_time': TR value in seconds
    """
    data_path = _download_subject_data(subject_id, "fmri")
    
    # Expected file patterns (HCP standard)
    # HCP preprocessed data usually has specific naming conventions
    nifti_path = data_path / f"{subject_id}_hp2000_clean.nii.gz"
    if not nifti_path.exists():
        # Try generic pattern
        nifti_path = list(data_path.glob("*func*.nii.gz"))
        if nifti_path:
            nifti_path = nifti_path[0]
        else:
            raise FileNotFoundError(f"No fMRI nifti file found for {subject_id}")
    
    img = nib.load(nifti_path)
    
    metadata = {}
    tr = 0.72 # HCP standard TR, fallback
    
    json_path = data_path / f"{nifti_path.stem}.json"
    if json_path.exists():
        with open(json_path, 'r') as f:
            metadata = json.load(f)
            if 'RepetitionTime' in metadata:
                tr = metadata['RepetitionTime']
    
    return {
        "nifti": img,
        "metadata": metadata,
        "subject_id": subject_id,
        "repetition_time": tr,
        "data": img.get_fdata(),
        "shape": img.shape
    }

def load_hcp_data(
    subject_id: str, 
    modalities: Optional[list] = None
) -> Dict[str, Any]:
    """
    Load specified modalities for a subject.
    
    Args:
        subject_id: HCP subject ID
        modalities: List of modalities to load, e.g. ['dmri', 'fmri'].
                   If None, loads both.
                   
    Returns:
        Dictionary with keys 'dmri' and/or 'fmri' containing the respective data dicts.
    """
    if modalities is None:
        modalities = ['dmri', 'fmri']
    
    result = {}
    
    if 'dmri' in modalities:
        result['dmri'] = load_hcp_dmri(subject_id)
        
    if 'fmri' in modalities:
        result['fmri'] = load_hcp_fmri(subject_id)
        
    return result
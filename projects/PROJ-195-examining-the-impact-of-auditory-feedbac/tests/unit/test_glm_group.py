"""
Unit tests for glm_group.py (Task T024).

Tests:
  1. One-sample t-test logic verification (against zero).
  2. FDR thresholding correctness.
  3. Cluster extraction and edge case handling (no clusters).
  4. Integration with valid_subjects.txt and contrast map loading.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import json

import numpy as np
import nibabel as nib
import pytest
from scipy import stats

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from glm_group import load_contrast_maps, run_group_analysis, main
from utils import get_bids_subject_path

# Fixtures
@pytest.fixture
def temp_project_dir():
    """Create a temporary project structure for testing."""
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    
    # Create directory structure
    (temp_path / 'data' / 'processed').mkdir(parents=True)
    (temp_path / 'data' / 'derivatives' / 'group_analysis').mkdir(parents=True)
    
    # Create mock valid_subjects.txt
    subjects = ['sub-01', 'sub-02', 'sub-03']
    with open(temp_path / 'data' / 'processed' / 'valid_subjects.txt', 'w') as f:
        f.write('\n'.join(subjects))
    
    # Create mock contrast maps (random data with known mean > 0)
    for sub in subjects:
        # Generate random data with a positive mean to ensure t-test passes
        data = np.random.randn(10, 10, 10) + 2.0  # Mean = 2.0
        img = nib.Nifti1Image(data.astype(np.float32), np.eye(4))
        img.to_filename(temp_path / 'data' / 'processed' / f"{sub}_contrast_perturbed.nii.gz")
    
    return temp_path

@pytest.fixture
def cleanup_temp(temp_project_dir):
    yield temp_project_dir
    shutil.rmtree(temp_project_dir)


class TestLoadContrastMaps:
    def test_load_contrast_maps_success(self, temp_project_dir):
        """Test that load_contrast_maps correctly finds and returns paths."""
        # Temporarily change the global variable in glm_group
        import glm_group
        original_processed = glm_group.PROCESSED_DIR
        original_valid = glm_group.VALID_SUBJECTS_FILE
        
        glm_group.PROCESSED_DIR = temp_project_dir / 'data' / 'processed'
        glm_group.VALID_SUBJECTS_FILE = temp_project_dir / 'data' / 'processed' / 'valid_subjects.txt'
        
        try:
            maps = load_contrast_maps()
            assert len(maps) == 3
            assert all('sub-0' in str(m) for m in maps)
            assert all(m.exists() for m in maps)
        finally:
            glm_group.PROCESSED_DIR = original_processed
            glm_group.VALID_SUBJECTS_FILE = original_valid

    def test_load_contrast_maps_missing_file(self, temp_project_dir):
        """Test error handling when valid_subjects.txt is missing."""
        import glm_group
        original_valid = glm_group.VALID_SUBJECTS_FILE
        
        glm_group.VALID_SUBJECTS_FILE = temp_project_dir / 'nonexistent.txt'
        
        try:
            with pytest.raises(FileNotFoundError):
                load_contrast_maps()
        finally:
            glm_group.VALID_SUBJECTS_FILE = original_valid


class TestRunGroupAnalysis:
    def test_one_sample_ttest_logic(self, temp_project_dir):
        """
        Verify that the one-sample t-test is actually testing against zero.
        We generate data with a known positive mean. The t-stat should be positive.
        """
        import glm_group
        original_processed = glm_group.PROCESSED_DIR
        original_output = glm_group.OUTPUT_DIR
        
        glm_group.PROCESSED_DIR = temp_project_dir / 'data' / 'processed'
        glm_group.VALID_SUBJECTS_FILE = temp_project_dir / 'data' / 'processed' / 'valid_subjects.txt'
        glm_group.OUTPUT_DIR = temp_project_dir / 'data' / 'derivatives' / 'group_analysis'
        
        try:
            maps = load_contrast_maps()
            results = run_group_analysis(maps)
            
            assert results['status'] == 'success'
            assert 'stat_map' in results
            assert 'thresholded_map' in results
            assert results['num_clusters'] > 0  # With mean=2.0, we expect clusters
            
            # Verify the stat map exists and has positive values
            stat_img = nib.load(results['stat_map'])
            stat_data = stat_img.get_fdata()
            assert np.mean(stat_data) > 0  # Should be positive given our input data
            
        finally:
            glm_group.PROCESSED_DIR = original_processed
            glm_group.OUTPUT_DIR = original_output

    def test_fdr_thresholding(self, temp_project_dir):
        """Test that FDR thresholding is applied correctly."""
        import glm_group
        original_processed = glm_group.PROCESSED_DIR
        original_output = glm_group.OUTPUT_DIR
        
        glm_group.PROCESSED_DIR = temp_project_dir / 'data' / 'processed'
        glm_group.VALID_SUBJECTS_FILE = temp_project_dir / 'data' / 'processed' / 'valid_subjects.txt'
        glm_group.OUTPUT_DIR = temp_project_dir / 'data' / 'derivatives' / 'group_analysis'
        
        try:
            maps = load_contrast_maps()
            results = run_group_analysis(maps)
            
            # Check that FDR threshold is reasonable (between 0 and 10 for Z-maps)
            assert 0 < results['fdr_threshold'] < 10
            
            # Verify the thresholded map exists
            assert Path(results['thresholded_map']).exists()
            
        finally:
            glm_group.PROCESSED_DIR = original_processed
            glm_group.OUTPUT_DIR = original_output

    def test_no_clusters_edge_case(self, temp_project_dir):
        """
        Test handling when no clusters survive FDR.
        We generate data with mean ~0 to trigger this.
        """
        import glm_group
        original_processed = glm_group.PROCESSED_DIR
        original_output = glm_group.OUTPUT_DIR
        
        # Generate null data (mean = 0)
        subjects = ['sub-01', 'sub-02', 'sub-03']
        for sub in subjects:
            data = np.random.randn(10, 10, 10)  # Mean ~ 0
            img = nib.Nifti1Image(data.astype(np.float32), np.eye(4))
            img.to_filename(temp_project_dir / 'data' / 'processed' / f"{sub}_contrast_perturbed.nii.gz")
        
        glm_group.PROCESSED_DIR = temp_project_dir / 'data' / 'processed'
        glm_group.VALID_SUBJECTS_FILE = temp_project_dir / 'data' / 'processed' / 'valid_subjects.txt'
        glm_group.OUTPUT_DIR = temp_project_dir / 'data' / 'derivatives' / 'group_analysis'
        
        try:
            maps = load_contrast_maps()
            results = run_group_analysis(maps)
            
            # Should return null_result status
            assert results['status'] == 'null_result'
            assert 'No clusters survived FDR' in results['message']
            
        finally:
            glm_group.PROCESSED_DIR = original_processed
            glm_group.OUTPUT_DIR = original_output


class TestMain:
    def test_main_execution(self, temp_project_dir):
        """Test that main() runs without error and returns 0."""
        import glm_group
        original_processed = glm_group.PROCESSED_DIR
        original_output = glm_group.OUTPUT_DIR
        original_valid = glm_group.VALID_SUBJECTS_FILE
        
        glm_group.PROCESSED_DIR = temp_project_dir / 'data' / 'processed'
        glm_group.VALID_SUBJECTS_FILE = temp_project_dir / 'data' / 'processed' / 'valid_subjects.txt'
        glm_group.OUTPUT_DIR = temp_project_dir / 'data' / 'derivatives' / 'group_analysis'
        
        try:
            exit_code = main()
            assert exit_code == 0
            assert (temp_project_dir / 'data' / 'derivatives' / 'group_analysis' / 'analysis_summary.json').exists()
        finally:
            glm_group.PROCESSED_DIR = original_processed
            glm_group.OUTPUT_DIR = original_output
            glm_group.VALID_SUBJECTS_FILE = original_valid

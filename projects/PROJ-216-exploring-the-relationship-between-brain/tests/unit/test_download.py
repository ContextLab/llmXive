"""
Unit tests for the download module.

These tests verify:
- Subject list extraction from directory structures
- Dataset priority ordering
- Sample limit enforcement
- Graceful handling of missing datasets
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Import the module under test
sys.path.insert(0, 'code')
from download import get_subject_list, validate_and_aggregate, OPENNEURO_DATASETS

class TestDownload:
    """Test cases for download functionality."""

    @pytest.fixture
    def temp_dataset_dir(self):
        """Create a temporary directory structure mimicking an OpenNeuro dataset."""
        temp_dir = tempfile.mkdtemp()
        dataset_dir = Path(temp_dir) / 'ds000224'
        dataset_dir.mkdir()
        
        # Create dataset_description.json to make it look valid
        desc_file = dataset_dir / 'dataset_description.json'
        desc_file.write_text(json.dumps({'Name': 'Test Dataset', 'DatasetType': 'raw'}))
        
        # Create subject folders with functional data
        for i in range(1, 6):
            subject_dir = dataset_dir / f'sub-{i:02d}'
            subject_dir.mkdir()
            func_dir = subject_dir / 'func'
            func_dir.mkdir()
            # Create a dummy BOLD file
            bold_file = func_dir / f'sub-{i:02d}_task-rest_bold.nii.gz'
            bold_file.write_text('dummy nifti data')
        
        # Create one subject without functional data (should be skipped)
        bad_subject_dir = dataset_dir / 'sub-99'
        bad_subject_dir.mkdir()
        
        return temp_dir

    def test_get_subject_list_valid_subjects(self, temp_dataset_dir):
        """Test that get_subject_list correctly identifies valid subjects."""
        dataset_dir = Path(temp_dataset_dir) / 'ds000224'
        subjects = get_subject_list(dataset_dir, 'ds000224')
        
        assert len(subjects) == 5
        assert '01' in subjects
        assert '05' in subjects
        assert '99' not in subjects  # Should be excluded (no func data)

    def test_get_subject_list_empty_directory(self):
        """Test handling of non-existent directory."""
        subjects = get_subject_list(Path('/nonexistent/path'), 'ds000224')
        assert subjects == []

    def test_validate_and_aggregate_respects_sample_limit(self, temp_dataset_dir):
        """Test that validate_and_aggregate enforces the sample limit."""
        dataset_path = Path(temp_dataset_dir) / 'ds000224'
        
        # Mock the behavioral data check to always succeed
        with patch('download.pd.read_csv') as mock_read_csv:
            mock_df = MagicMock()
            mock_df.columns = ['Fluid_Intelligence']
            mock_df.__getitem__ = lambda self, key: [25.5] if key == 'Fluid_Intelligence' else []
            mock_read_csv.return_value = mock_df
            
            downloaded = {'ds000224': dataset_path}
            subjects, count = validate_and_aggregate(downloaded, sample_limit=3)
            
            assert count == 3
            assert len(subjects) == 3

    def test_validate_and_aggregate_handles_missing_behavioral_data(self, temp_dataset_dir):
        """Test that subjects without behavioral data are excluded."""
        dataset_path = Path(temp_dataset_dir) / 'ds000224'
        
        # Mock read_csv to raise exception (simulating no behavioral data)
        with patch('download.pd.read_csv', side_effect=Exception("No data")):
            downloaded = {'ds000224': dataset_path}
            subjects, count = validate_and_aggregate(downloaded, sample_limit=10)
            
            assert count == 0
            assert len(subjects) == 0

    def test_dataset_priority_ordering(self):
        """Test that datasets are processed in priority order."""
        # Verify the priority values in the constant
        assert OPENNEURO_DATASETS['ds000224']['priority'] == 1
        assert OPENNEURO_DATASETS['ds000230']['priority'] == 2

    def test_validate_and_aggregate_graceful_missing_dataset(self):
        """Test handling when a dataset directory doesn't exist."""
        downloaded = {'ds000224': Path('/nonexistent/ds000224')}
        subjects, count = validate_and_aggregate(downloaded, sample_limit=10)
        
        assert count == 0
        assert len(subjects) == 0

    def test_validate_and_aggregate_empty_dataset(self):
        """Test handling of a dataset with no valid subjects."""
        temp_dir = tempfile.mkdtemp()
        try:
            dataset_path = Path(temp_dir) / 'ds000224'
            dataset_path.mkdir()
            # No subjects created
            
            downloaded = {'ds000224': dataset_path}
            subjects, count = validate_and_aggregate(downloaded, sample_limit=10)
            
            assert count == 0
            assert len(subjects) == 0
        finally:
            shutil.rmtree(temp_dir)
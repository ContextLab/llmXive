"""
Unit tests for T012c: Match resistance metadata and filter studies.
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
import pandas as pd

from data.match_and_download import (
    load_manifest,
    check_metadata_in_preview,
    has_resistance_metadata,
    has_temporal_metadata,
    filter_studies_by_metadata,
    DataAvailabilityError
)
from utils.exceptions import DataAvailabilityError as DataAvailabilityErrorClass

class TestT012c:
    """Tests for T012c functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manifest_path = Path(self.temp_dir) / 'test_manifest.json'
        
        # Create a test manifest
        self.test_studies = [
            {
                'study_id': 'PMD001',
                'title': 'Test Study 1',
                'download_url': 'https://example.com/study1'
            },
            {
                'study_id': 'PMD002',
                'title': 'Test Study 2',
                'download_url': 'https://example.com/study2'
            }
        ]
        
        with open(self.manifest_path, 'w') as f:
            json.dump(self.test_studies, f)

    def teardown_method(self):
        """Cleanup test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_manifest(self):
        """Test loading manifest from JSON file."""
        studies = load_manifest(self.manifest_path)
        assert len(studies) == 2
        assert studies[0]['study_id'] == 'PMD001'

    def test_load_manifest_missing_file(self):
        """Test loading manifest when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_manifest(Path('/nonexistent/path.json'))

    def test_check_metadata_in_preview(self):
        """Test checking metadata in phenotype preview."""
        # Test with resistance column
        preview_with_resistance = {'phenotype': 'resistant', 'other': 'data'}
        assert check_metadata_in_preview(preview_with_resistance, ['phenotype']) is True
        
        # Test without resistance column
        preview_without_resistance = {'other': 'data', 'another': 'field'}
        assert check_metadata_in_preview(preview_without_resistance, ['phenotype']) is False
        
        # Test with None preview
        assert check_metadata_in_preview(None, ['phenotype']) is False

    def test_has_resistance_metadata(self):
        """Test resistance metadata detection."""
        # With resistance column
        preview = {'resistance_score': 0.8, 'other': 'data'}
        assert has_resistance_metadata(preview) is True
        
        # Without resistance column
        preview = {'other': 'data', 'another': 'field'}
        assert has_resistance_metadata(preview) is False

    def test_has_temporal_metadata(self):
        """Test temporal metadata detection."""
        # With temporal column
        preview = {'timepoint': 'baseline', 'other': 'data'}
        assert has_temporal_metadata(preview) is True
        
        # Without temporal column
        preview = {'other': 'data', 'another': 'field'}
        assert has_temporal_metadata(preview) is False

    def test_filter_studies_by_metadata_with_local_files(self, monkeypatch):
        """Test filtering studies using local phenotype files."""
        # Create temporary raw data directory
        raw_dir = Path(self.temp_dir) / 'data' / 'raw'
        raw_dir.mkdir(parents=True)
        
        # Create phenotype files with required columns
        phenotype1 = pd.DataFrame({
            'phenotype': ['resistant', 'susceptible'],
            'timepoint': ['baseline', 'baseline']
        })
        phenotype1.to_csv(raw_dir / 'PMD001_phenotype.csv', index=False)
        
        phenotype2 = pd.DataFrame({
            'other_col': ['data1', 'data2'],
            'another_col': ['data3', 'data4']
        })
        phenotype2.to_csv(raw_dir / 'PMD002_phenotype.csv', index=False)
        
        # Mock the RAW_DATA_DIR constant
        import data.match_and_download as module
        original_dir = module.RAW_DATA_DIR
        module.RAW_DATA_DIR = raw_dir
        
        try:
            # Test filtering
            filtered = filter_studies_by_metadata(self.test_studies)
            
            # Only PMD001 should be valid (has both resistance and temporal)
            assert len(filtered) == 1
            assert filtered[0]['study_id'] == 'PMD001'
        finally:
            module.RAW_DATA_DIR = original_dir

    def test_filter_studies_raises_when_no_valid_studies(self, monkeypatch):
        """Test that DataAvailabilityError is raised when no studies match."""
        # Create temporary raw data directory
        raw_dir = Path(self.temp_dir) / 'data' / 'raw'
        raw_dir.mkdir(parents=True)
        
        # Create phenotype file without required columns
        phenotype = pd.DataFrame({
            'other_col': ['data1', 'data2'],
            'another_col': ['data3', 'data4']
        })
        phenotype.to_csv(raw_dir / 'PMD001_phenotype.csv', index=False)
        
        # Mock the RAW_DATA_DIR constant
        import data.match_and_download as module
        original_dir = module.RAW_DATA_DIR
        module.RAW_DATA_DIR = raw_dir
        
        try:
            # Test filtering - should raise DataAvailabilityError
            with pytest.raises(DataAvailabilityErrorClass):
                filter_studies_by_metadata(self.test_studies)
        finally:
            module.RAW_DATA_DIR = original_dir
import pytest
import os
import tempfile
from pathlib import Path
import pandas as pd
from unittest.mock import patch, MagicMock

# Add the code directory to the path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from preprocessing.download import (
    download_url_exists,
    process_metadata_and_exclude_subjects,
    RAW_DATA_DIR,
    METADATA_DIR,
    PARTICIPANTS_FILE,
    EXCLUSION_LOG_FILE,
    SUBJECT_STATUS_FILE
)

class TestDownloadURLExists:
    """Tests for the download_url_exists function."""
    
    @patch('preprocessing.download.requests.head')
    def test_url_exists(self, mock_head):
        """Test that a valid URL returns True."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response
        
        result = download_url_exists('https://example.com/valid')
        assert result is True
        mock_head.assert_called_once_with('https://example.com/valid', timeout=30)
    
    @patch('preprocessing.download.requests.head')
    def test_url_not_exists(self, mock_head):
        """Test that an invalid URL returns False."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_head.return_value = mock_response
        
        result = download_url_exists('https://example.com/invalid')
        assert result is False
    
    @patch('preprocessing.download.requests.head')
    def test_url_timeout(self, mock_head):
        """Test that a timeout returns False."""
        mock_head.side_effect = Exception("Timeout")
        
        result = download_url_exists('https://example.com/timeout')
        assert result is False

class TestProcessMetadataAndExcludeSubjects:
    """Tests for the process_metadata_and_exclude_subjects function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary directories
        self.temp_dir = tempfile.TemporaryDirectory()
        self.raw_data_dir = Path(self.temp_dir.name) / 'raw'
        self.metadata_dir = Path(self.temp_dir.name) / 'metadata'
        self.raw_data_dir.mkdir()
        self.metadata_dir.mkdir()
        
        # Create a test participants file
        self.participants_path = self.raw_data_dir / PARTICIPANTS_FILE
        test_data = {
            'participant_id': ['sub-01', 'sub-02', 'sub-03', 'sub-04'],
            'age': [25, 30, 35, 40],
            'sex': ['M', 'F', 'M', 'F'],
            'group': ['control', 'schizophrenia', '', 'nan']
        }
        df = pd.DataFrame(test_data)
        df.to_csv(self.participants_path, sep='\t', index=False)
        
        # Temporarily override the global paths
        self.original_raw_dir = RAW_DATA_DIR
        self.original_meta_dir = METADATA_DIR
        RAW_DATA_DIR.__class__ = type('Path', (Path,), {'__new__': lambda cls, path: self.raw_data_dir})
        METADATA_DIR.__class__ = type('Path', (Path,), {'__new__': lambda cls, path: self.metadata_dir})
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
        # Restore original paths
        RAW_DATA_DIR.__class__ = Path
        METADATA_DIR.__class__ = Path
    
    def test_excludes_subjects_with_missing_labels(self):
        """Test that subjects with missing diagnostic labels are excluded."""
        excluded_count, included_count = process_metadata_and_exclude_subjects()
        
        # Should exclude 2 subjects (sub-03 with empty string, sub-04 with 'nan')
        assert excluded_count == 2
        assert included_count == 2
        
        # Check that exclusion log was created
        exclusion_log_path = self.metadata_dir / EXCLUSION_LOG_FILE
        assert exclusion_log_path.exists()
        
        # Check that subject status file was created
        subject_status_path = self.metadata_dir / SUBJECT_STATUS_FILE
        assert subject_status_path.exists()
        
        # Verify the content of subject status file
        df_status = pd.read_csv(subject_status_path)
        assert len(df_status) == 4
        
        # Check that sub-01 and sub-02 are included
        included = df_status[df_status['status'] == 'included']
        assert len(included) == 2
        assert 'sub-01' in included['subject_id'].values
        assert 'sub-02' in included['subject_id'].values
        
        # Check that sub-03 and sub-04 are excluded
        excluded = df_status[df_status['status'] == 'excluded']
        assert len(excluded) == 2
        assert 'sub-03' in excluded['subject_id'].values
        assert 'sub-04' in excluded['subject_id'].values
    
    def test_exclusion_log_content(self):
        """Test that the exclusion log contains the correct information."""
        process_metadata_and_exclude_subjects()
        
        exclusion_log_path = self.metadata_dir / EXCLUSION_LOG_FILE
        with open(exclusion_log_path, 'r') as f:
            content = f.read()
        
        # Check that the log contains expected information
        assert 'Exclusion Log' in content
        assert 'Dataset' in content
        assert 'Excluded subjects: 2' in content
        assert 'Included subjects: 2' in content
        assert 'sub-03' in content
        assert 'sub-04' in content
        assert 'Missing diagnostic label' in content
    
    def test_no_diagnostic_column(self):
        """Test behavior when no diagnostic column is found."""
        # Create a participants file without diagnostic column
        test_data = {
            'participant_id': ['sub-01', 'sub-02'],
            'age': [25, 30],
            'sex': ['M', 'F']
        }
        df = pd.DataFrame(test_data)
        df.to_csv(self.participants_path, sep='\t', index=False)
        
        excluded_count, included_count = process_metadata_and_exclude_subjects()
        
        # All subjects should be excluded when no diagnostic column is found
        assert excluded_count == 2
        assert included_count == 0
        
        # Check exclusion log
        exclusion_log_path = self.metadata_dir / EXCLUSION_LOG_FILE
        with open(exclusion_log_path, 'r') as f:
            content = f.read()
        
        assert 'No diagnostic label column found' in content
        assert 'All subjects will be excluded' in content

"""
Unit tests for download.py checksum verification.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from download import (
    ChecksumError,
    compute_sha256,
    validate_checksum,
    filter_dataset_columns,
    write_exclusion_log,
    update_readme_status
)


class TestChecksumVerification:
    """Test checksum computation and validation."""
    
    def test_compute_sha256(self):
        """Test SHA256 computation on a known file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)
        
        try:
            checksum = compute_sha256(temp_path)
            # Known SHA256 for "test content"
            expected = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
            assert checksum == expected
        finally:
            temp_path.unlink()
    
    def test_validate_checksum_success(self):
        """Test successful checksum validation."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)
        
        try:
            # Should not raise
            validate_checksum(temp_path)
        finally:
            temp_path.unlink()
    
    def test_validate_checksum_mismatch(self):
        """Test checksum validation with mismatch."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ChecksumError):
                validate_checksum(temp_path, expected_checksum="wrong_checksum")
        finally:
            temp_path.unlink()
    
    def test_validate_checksum_file_not_found(self):
        """Test checksum validation on non-existent file."""
        with pytest.raises(FileNotFoundError):
            validate_checksum(Path("/nonexistent/file.txt"))

class TestColumnFiltering:
    """Test dataset column filtering."""
    
    def test_all_columns_present(self):
        """Test when all required columns are present."""
        import pandas as pd
        df = pd.DataFrame({
            'duration_estimate': [1, 2, 3],
            'stimulus_sequence': ['a', 'b', 'c'],
            'participant_id': [1, 2, 3]
        })
        
        has_all, missing = filter_dataset_columns(df, ['duration_estimate', 'stimulus_sequence', 'participant_id'])
        assert has_all is True
        assert missing == []
    
    def test_missing_columns(self):
        """Test when some required columns are missing."""
        import pandas as pd
        df = pd.DataFrame({
            'duration_estimate': [1, 2, 3],
            'stimulus_sequence': ['a', 'b', 'c']
        })
        
        has_all, missing = filter_dataset_columns(df, ['duration_estimate', 'stimulus_sequence', 'participant_id'])
        assert has_all is False
        assert missing == ['participant_id']

class TestExclusionLogging:
    """Test exclusion log functionality."""
    
    def test_write_exclusion_log(self):
        """Test writing exclusion log entry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'exclusion_log.json'
            
            write_exclusion_log(log_path, 'dataset_1', 'Missing columns')
            
            with open(log_path, 'r') as f:
                log = json.load(f)
            
            assert len(log) == 1
            assert log[0]['dataset_id'] == 'dataset_1'
            assert log[0]['reason'] == 'Missing columns'
            assert 'timestamp' in log[0]
    
    def test_append_to_existing_log(self):
        """Test appending to existing exclusion log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'exclusion_log.json'
            
            # Create initial log
            write_exclusion_log(log_path, 'dataset_1', 'Reason 1')
            write_exclusion_log(log_path, 'dataset_2', 'Reason 2')
            
            with open(log_path, 'r') as f:
                log = json.load(f)
            
            assert len(log) == 2
            assert log[0]['dataset_id'] == 'dataset_1'
            assert log[1]['dataset_id'] == 'dataset_2'

class TestReadmeUpdates:
    """Test README update functionality."""
    
    def test_update_readme_status_valid(self):
        """Test updating README with valid status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            readme_path = Path(tmpdir) / 'README.md'
            readme_content = """# Data Directory
            
            ### Dataset Status
            - dataset_1: excluded
              reason: Old reason
            """
            readme_path.write_text(readme_content)
            
            update_readme_status(readme_path, 'dataset_1', 'valid')
            
            updated_content = readme_path.read_text()
            assert '- dataset_1: valid' in updated_content
    
    def test_update_readme_status_excluded(self):
        """Test updating README with excluded status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            readme_path = Path(tmpdir) / 'README.md'
            readme_content = """# Data Directory
            
            ### Dataset Status
            - dataset_1: valid
            """
            readme_path.write_text(readme_content)
            
            update_readme_status(readme_path, 'dataset_1', 'excluded', 'Missing columns')
            
            updated_content = readme_path.read_text()
            assert '- dataset_1: excluded' in updated_content
            assert 'reason: Missing columns' in updated_content
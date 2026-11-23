import pytest
import numpy as np
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd

# Import the function to test
# Assuming the file is in code/entropy.py
import sys
sys.path.insert(0, 'code')
from entropy import flag_invalid_parcels, process_parcels_for_subject

class TestFlagInvalidParcels:
    @pytest.fixture
    def temp_log_dir(self):
        """Create a temporary directory for logs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            log_dir.mkdir()
            yield log_dir

    def test_flag_subject_with_high_nan_ratio(self, temp_log_dir):
        """Test that a subject with >10% NaN parcels is flagged and logged."""
        # Create mock data: 100 parcels, 15 NaN (15%)
        parcel_results = {i: 1.0 if i < 85 else np.nan for i in range(100)}
        subject_id = "SUBJ_001"
        
        # Mock Config to point to temp log dir
        with patch('entropy.config') as mock_config:
            mock_config.DATA_DIR = str(temp_log_dir.parent)
            
            # Run flagging
            is_flagged = flag_invalid_parcels(subject_id, parcel_results, threshold_pct=0.10)
            
            assert is_flagged is True
            
            # Check log file
            log_file = temp_log_dir / "invalid_parcels.log"
            assert log_file.exists()
            
            content = log_file.read_text()
            assert subject_id in content
            assert "15/100" in content
            assert "15.00%" in content

    def test_dont_flag_subject_with_low_nan_ratio(self, temp_log_dir):
        """Test that a subject with <=10% NaN parcels is NOT flagged."""
        # Create mock data: 100 parcels, 5 NaN (5%)
        parcel_results = {i: 1.0 if i < 95 else np.nan for i in range(100)}
        subject_id = "SUBJ_002"
        
        with patch('entropy.config') as mock_config:
            mock_config.DATA_DIR = str(temp_log_dir.parent)
            
            is_flagged = flag_invalid_parcels(subject_id, parcel_results, threshold_pct=0.10)
            
            assert is_flagged is False
            
            # Log file should not exist or not contain this subject
            log_file = temp_log_dir / "invalid_parcels.log"
            if log_file.exists():
                content = log_file.read_text()
                assert subject_id not in content

    def test_empty_parcel_results(self, temp_log_dir):
        """Test handling of empty parcel results."""
        parcel_results = {}
        subject_id = "SUBJ_003"
        
        with patch('entropy.config') as mock_config:
            mock_config.DATA_DIR = str(temp_log_dir.parent)
            
            is_flagged = flag_invalid_parcels(subject_id, parcel_results, threshold_pct=0.10)
            
            assert is_flagged is False

    def test_all_nan_parcels(self, temp_log_dir):
        """Test handling of all NaN parcels (100% invalid)."""
        parcel_results = {i: np.nan for i in range(50)}
        subject_id = "SUBJ_004"
        
        with patch('entropy.config') as mock_config:
            mock_config.DATA_DIR = str(temp_log_dir.parent)
            
            is_flagged = flag_invalid_parcels(subject_id, parcel_results, threshold_pct=0.10)
            
            assert is_flagged is True
            
            log_file = temp_log_dir / "invalid_parcels.log"
            assert log_file.exists()
            content = log_file.read_text()
            assert "50/50" in content
            assert "100.00%" in content

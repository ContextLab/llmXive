import pytest
import csv
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.data.acquisition import main as run_interpolation_validation
from src.utils.config import get_missing_threshold_percent

class TestT015eValidation:
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.interim_dir = Path(self.temp_dir)
        self.noise_mapped_path = self.interim_dir / "noise_mapped.csv"
        
        # Create mock data
        self.mock_records = [
            {'recording_id': '1', 'species_id': 'sp1', 'latitude': 1.0, 'longitude': 1.0, 'noise_level_db': 50.0, 'noise_source': 'global_soundscapes'},
            {'recording_id': '2', 'species_id': 'sp2', 'latitude': 2.0, 'longitude': 2.0, 'noise_level_db': 55.0, 'noise_source': 'interpolated'},
            {'recording_id': '3', 'species_id': 'sp3', 'latitude': 3.0, 'longitude': 3.0, 'noise_level_db': None, 'noise_source': 'interpolation_failed'},
            {'recording_id': '4', 'species_id': 'sp4', 'latitude': 4.0, 'longitude': 4.0, 'noise_level_db': None, 'noise_source': 'missing_coords'},
            {'recording_id': '5', 'species_id': 'sp5', 'latitude': 5.0, 'longitude': 5.0, 'noise_level_db': None, 'noise_source': 'missing'},
        ]
        
        # Write mock data
        with open(self.noise_mapped_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.mock_records[0].keys())
            writer.writeheader()
            for rec in self.mock_records:
                writer.writerow(rec)

    def test_validation_log_creation(self):
        """Test that the validation log is created."""
        # Mock the config functions to use our temp dir
        with patch('src.data.acquisition.get_project_root', return_value=Path(self.temp_dir).parent):
            with patch('src.data.acquisition.get_interim_data_dir', return_value=self.interim_dir):
                with patch('src.data.acquisition.get_missing_threshold_percent', return_value=10):
                    result = run_interpolation_validation()
                    
        validation_log_path = self.interim_dir / "interpolation_validation_log.csv"
        assert validation_log_path.exists()
        
        with open(validation_log_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == len(self.mock_records)

    def test_failure_rate_calculation(self):
        """Test that failure rate is calculated correctly."""
        # 2 failures: 'interpolation_failed' (rec 3) and 'missing' (rec 5). 
        # 'missing_coords' (rec 4) is not counted as a failure of interpolation.
        # Total records = 5.
        # Failure rate = 2/5 = 0.4 = 40%
        
        with patch('src.data.acquisition.get_project_root', return_value=Path(self.temp_dir).parent):
            with patch('src.data.acquisition.get_interim_data_dir', return_value=self.interim_dir):
                with patch('src.data.acquisition.get_missing_threshold_percent', return_value=10):
                    result = run_interpolation_validation()
                    
        assert result['total_records'] == 5
        assert result['failed'] == 2
        assert abs(result['failure_rate'] - 0.4) < 0.01

    def test_warning_on_high_failure_rate(self):
        """Test that a warning is logged if failure rate > threshold."""
        # Threshold is 10%, failure rate is 40% -> should warn
        with patch('src.data.acquisition.get_project_root', return_value=Path(self.temp_dir).parent):
            with patch('src.data.acquisition.get_interim_data_dir', return_value=self.interim_dir):
                with patch('src.data.acquisition.get_missing_threshold_percent', return_value=10):
                    result = run_interpolation_validation()
                    
        assert result['status'] == 'warning'

    def test_ok_on_low_failure_rate(self):
        """Test that status is ok if failure rate <= threshold."""
        # Modify mock data to have only 1 failure out of 5 -> 20% (still > 10% with threshold 10)
        # Let's make it 1 failure out of 10 -> 10% -> ok
        mock_records_ok = self.mock_records[:4] + [
            {'recording_id': '6', 'species_id': 'sp6', 'latitude': 6.0, 'longitude': 6.0, 'noise_level_db': 60.0, 'noise_source': 'global_soundscapes'},
            {'recording_id': '7', 'species_id': 'sp7', 'latitude': 7.0, 'longitude': 7.0, 'noise_level_db': 65.0, 'noise_source': 'global_soundscapes'},
            {'recording_id': '8', 'species_id': 'sp8', 'latitude': 8.0, 'longitude': 8.0, 'noise_level_db': 70.0, 'noise_source': 'global_soundscapes'},
            {'recording_id': '9', 'species_id': 'sp9', 'latitude': 9.0, 'longitude': 9.0, 'noise_level_db': 75.0, 'noise_source': 'global_soundscapes'},
            {'recording_id': '10', 'species_id': 'sp10', 'latitude': 10.0, 'longitude': 10.0, 'noise_level_db': 80.0, 'noise_source': 'global_soundscapes'},
        ]
        
        with open(self.noise_mapped_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=mock_records_ok[0].keys())
            writer.writeheader()
            for rec in mock_records_ok:
                writer.writerow(rec)
        
        with patch('src.data.acquisition.get_project_root', return_value=Path(self.temp_dir).parent):
            with patch('src.data.acquisition.get_interim_data_dir', return_value=self.interim_dir):
                with patch('src.data.acquisition.get_missing_threshold_percent', return_value=20): # 1/10 = 10% <= 20%
                    result = run_interpolation_validation()
                    
        assert result['status'] == 'ok'
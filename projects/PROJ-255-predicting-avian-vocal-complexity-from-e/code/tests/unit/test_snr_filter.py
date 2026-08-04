import pytest
import os
import csv
import tempfile
from pathlib import Path
from src.data.preprocessing import filter_by_snr_threshold, load_csv, save_csv

class TestSNRFilter:
    @pytest.fixture
    def sample_data(self):
        return [
            {'record_id': '1', 'species_id': 'A', 'location_id': 'L1', 'snr_db': '15.0', 'noise_level_db': '40.0'},
            {'record_id': '2', 'species_id': 'A', 'location_id': 'L1', 'snr_db': '5.0', 'noise_level_db': '50.0'},
            {'record_id': '3', 'species_id': 'B', 'location_id': 'L2', 'snr_db': '20.0', 'noise_level_db': '30.0'},
            {'record_id': '4', 'species_id': 'B', 'location_id': 'L2', 'snr_db': '8.0', 'noise_level_db': '55.0'},
            {'record_id': '5', 'species_id': 'C', 'location_id': 'L3', 'snr_db': '10.0', 'noise_level_db': '45.0'},
        ]

    def test_filter_by_snr_threshold_keeps_high_snr(self, sample_data):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'input.csv'
            output_path = Path(tmpdir) / 'output.csv'
            dropped_path = Path(tmpdir) / 'dropped.csv'
            
            save_csv(input_path, sample_data)
            
            kept, dropped = filter_by_snr_threshold(input_path, output_path, dropped_path, threshold_db=10.0)
            
            assert len(kept) == 3
            assert len(dropped) == 2
            
            # Check kept records have SNR >= 10
            for record in kept:
                assert float(record['snr_db']) >= 10.0
            
            # Check dropped records have SNR < 10
            for record in dropped:
                assert float(record['data']['snr_db']) < 10.0

    def test_filter_by_snr_threshold_empty_input(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'input.csv'
            output_path = Path(tmpdir) / 'output.csv'
            dropped_path = Path(tmpdir) / 'dropped.csv'
            
            save_csv(input_path, [])
            
            kept, dropped = filter_by_snr_threshold(input_path, output_path, dropped_path, threshold_db=10.0)
            
            assert len(kept) == 0
            assert len(dropped) == 0

    def test_filter_by_snr_threshold_missing_snr_column(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'input.csv'
            output_path = Path(tmpdir) / 'output.csv'
            dropped_path = Path(tmpdir) / 'dropped.csv'
            
            data = [{'record_id': '1', 'species_id': 'A'}]
            save_csv(input_path, data)
            
            with pytest.raises(ValueError, match="Input file must contain"):
                filter_by_snr_threshold(input_path, output_path, dropped_path, threshold_db=10.0)

    def test_filter_by_snr_threshold_invalid_snr_value(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'input.csv'
            output_path = Path(tmpdir) / 'output.csv'
            dropped_path = Path(tmpdir) / 'dropped.csv'
            
            data = [
                {'record_id': '1', 'snr_db': 'invalid'},
                {'record_id': '2', 'snr_db': '15.0'},
            ]
            save_csv(input_path, data)
            
            kept, dropped = filter_by_snr_threshold(input_path, output_path, dropped_path, threshold_db=10.0)
            
            assert len(kept) == 1
            assert len(dropped) == 1
            assert dropped[0]['reason'] == 'invalid_snr'

    def test_filter_by_snr_threshold_output_files_created(self, sample_data):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'input.csv'
            output_path = Path(tmpdir) / 'output.csv'
            dropped_path = Path(tmpdir) / 'dropped.csv'
            
            save_csv(input_path, sample_data)
            
            filter_by_snr_threshold(input_path, output_path, dropped_path, threshold_db=10.0)
            
            assert output_path.exists()
            assert dropped_path.exists()
            
            output_data = load_csv(output_path)
            dropped_data = load_csv(dropped_path)
            
            assert len(output_data) == 3
            assert len(dropped_data) == 2
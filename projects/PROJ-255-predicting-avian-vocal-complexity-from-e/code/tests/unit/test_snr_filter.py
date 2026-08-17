import os
import csv
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.data.preprocessing import filter_by_snr_threshold, load_csv, save_csv


class TestSNRFilter:
    @pytest.fixture
    def temp_csv_file(self):
        """Create a temporary CSV file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=['recording_id', 'species_id', 'snr_db', 'latitude', 'longitude'])
            writer.writeheader()
            writer.writerow({
                'recording_id': 'rec_001',
                'species_id': 'species_A',
                'snr_db': '15.0',
                'latitude': '40.7128',
                'longitude': '-74.0060'
            })
            writer.writerow({
                'recording_id': 'rec_002',
                'species_id': 'species_B',
                'snr_db': '8.0',
                'latitude': '34.0522',
                'longitude': '-118.2437'
            })
            writer.writerow({
                'recording_id': 'rec_003',
                'species_id': 'species_A',
                'snr_db': '12.0',
                'latitude': '40.7128',
                'longitude': '-74.0060'
            })
            writer.writerow({
                'recording_id': 'rec_004',
                'species_id': 'species_C',
                'snr_db': '5.0',
                'latitude': '51.5074',
                'longitude': '-0.1278'
            })
            writer.writerow({
                'recording_id': 'rec_005',
                'species_id': 'species_B',
                'snr_db': '10.0',
                'latitude': '34.0522',
                'longitude': '-118.2437'
            })
            temp_path = Path(f.name)
        yield temp_path
        temp_path.unlink()

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_filter_by_snr_threshold_keeps_above_threshold(self, temp_csv_file, temp_output_dir):
        """Test that records with SNR >= threshold are kept."""
        output_file = temp_output_dir / 'filtered.csv'
        exclusion_file = temp_output_dir / 'excluded.csv'
        threshold = 10.0

        kept, excluded = filter_by_snr_threshold(
            input_path=temp_csv_file,
            output_path=output_file,
            exclusion_log_path=exclusion_file,
            threshold_db=threshold
        )

        # Should keep rec_001 (15.0), rec_003 (12.0), rec_005 (10.0)
        assert len(kept) == 3
        kept_ids = [r['recording_id'] for r in kept]
        assert 'rec_001' in kept_ids
        assert 'rec_003' in kept_ids
        assert 'rec_005' in kept_ids

        # Should exclude rec_002 (8.0), rec_004 (5.0)
        assert len(excluded) == 2
        excluded_ids = [r['recording_id'] for r in excluded]
        assert 'rec_002' in excluded_ids
        assert 'rec_004' in excluded_ids

    def test_filter_by_snr_threshold_excludes_below_threshold(self, temp_csv_file, temp_output_dir):
        """Test that records with SNR < threshold are excluded."""
        output_file = temp_output_dir / 'filtered.csv'
        exclusion_file = temp_output_dir / 'excluded.csv'
        threshold = 10.0

        kept, excluded = filter_by_snr_threshold(
            input_path=temp_csv_file,
            output_path=output_file,
            exclusion_log_path=exclusion_file,
            threshold_db=threshold
        )

        excluded_reasons = {r['recording_id']: r['reason'] for r in excluded}
        assert excluded_reasons['rec_002'] == 'snr_below_threshold'
        assert excluded_reasons['rec_004'] == 'snr_below_threshold'

    def test_filter_by_snr_threshold_boundary_case(self, temp_csv_file, temp_output_dir):
        """Test that records with SNR exactly equal to threshold are kept."""
        output_file = temp_output_dir / 'filtered.csv'
        exclusion_file = temp_output_dir / 'excluded.csv'
        threshold = 10.0

        kept, excluded = filter_by_snr_threshold(
            input_path=temp_csv_file,
            output_path=output_file,
            exclusion_log_path=exclusion_file,
            threshold_db=threshold
        )

        # rec_005 has SNR exactly 10.0, should be kept
        kept_ids = [r['recording_id'] for r in kept]
        assert 'rec_005' in kept_ids

    def test_filter_by_snr_threshold_creates_output_files(self, temp_csv_file, temp_output_dir):
        """Test that output files are created."""
        output_file = temp_output_dir / 'filtered.csv'
        exclusion_file = temp_output_dir / 'excluded.csv'

        filter_by_snr_threshold(
            input_path=temp_csv_file,
            output_path=output_file,
            exclusion_log_path=exclusion_file,
            threshold_db=10.0
        )

        assert output_file.exists()
        assert exclusion_file.exists()

    def test_filter_by_snr_threshold_invalid_snr(self, temp_output_dir):
        """Test handling of invalid SNR values."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=['recording_id', 'snr_db'])
            writer.writeheader()
            writer.writerow({'recording_id': 'rec_valid', 'snr_db': '15.0'})
            writer.writerow({'recording_id': 'rec_invalid', 'snr_db': 'NaN'})
            writer.writerow({'recording_id': 'rec_missing', 'snr_db': ''})
            input_file = Path(f.name)

        output_file = temp_output_dir / 'filtered.csv'
        exclusion_file = temp_output_dir / 'excluded.csv'

        kept, excluded = filter_by_snr_threshold(
            input_path=input_file,
            output_path=output_file,
            exclusion_log_path=exclusion_file,
            threshold_db=10.0
        )

        # Only valid record should be kept
        assert len(kept) == 1
        assert kept[0]['recording_id'] == 'rec_valid'

        # Invalid records should be excluded
        assert len(excluded) == 2
        excluded_ids = [r['recording_id'] for r in excluded]
        assert 'rec_invalid' in excluded_ids
        assert 'rec_missing' in excluded_ids

    def test_filter_by_snr_threshold_empty_input(self, temp_output_dir):
        """Test handling of empty input file."""
        input_file = temp_output_dir / 'empty_input.csv'
        output_file = temp_output_dir / 'filtered.csv'
        exclusion_file = temp_output_dir / 'excluded.csv'

        # Create empty CSV with headers
        input_file.parent.mkdir(parents=True, exist_ok=True)
        with open(input_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['recording_id', 'snr_db'])
            writer.writeheader()

        kept, excluded = filter_by_snr_threshold(
            input_path=input_file,
            output_path=output_file,
            exclusion_log_path=exclusion_file,
            threshold_db=10.0
        )

        assert len(kept) == 0
        assert len(excluded) == 0
        assert output_file.exists()
        assert exclusion_file.exists()

    def test_filter_by_snr_threshold_different_thresholds(self, temp_csv_file, temp_output_dir):
        """Test filtering with different thresholds."""
        output_file = temp_output_dir / 'filtered.csv'
        exclusion_file = temp_output_dir / 'excluded.csv'

        # Test with threshold 5.0
        kept_low, _ = filter_by_snr_threshold(
            input_path=temp_csv_file,
            output_path=output_file,
            exclusion_log_path=exclusion_file,
            threshold_db=5.0
        )
        assert len(kept_low) == 5  # All records have SNR >= 5.0

        # Test with threshold 15.0
        kept_high, _ = filter_by_snr_threshold(
            input_path=temp_csv_file,
            output_path=output_file,
            exclusion_log_path=exclusion_file,
            threshold_db=15.0
        )
        assert len(kept_high) == 1  # Only rec_001 has SNR >= 15.0
import pytest
import csv
import os
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from data_ingestion import validate_and_save_raw

class TestDataIngestionValidation:
    @pytest.fixture
    def temp_dirs(self, tmp_path):
        raw_dir = tmp_path / "data" / "raw"
        processed_dir = tmp_path / "data" / "processed"
        raw_dir.mkdir(parents=True)
        processed_dir.mkdir(parents=True)
        return raw_dir, processed_dir

    def test_valid_compositions_kept(self, temp_dirs):
        raw_dir, processed_dir = temp_dirs
        input_file = raw_dir / "input.csv"
        output_file = processed_dir / "output.csv"
        log_file = processed_dir / "log.csv"

        # Create input with valid glass formers (Rc < 100)
        with open(input_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['composition', 'critical_cooling_rate', 'gfa_label'])
            writer.writerow(['Fe 0.5, Cu 0.5', '50.0', 'Glass'])
            writer.writerow(['Zr 0.4, Cu 0.6', '80.0', 'Glass'])

        validate_and_save_raw(input_file, output_file, log_file)

        assert output_file.exists()
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert all(float(r['critical_cooling_rate']) < 100 for r in rows)

    def test_high_rc_filtered(self, temp_dirs):
        raw_dir, processed_dir = temp_dirs
        input_file = raw_dir / "input.csv"
        output_file = processed_dir / "output.csv"
        log_file = processed_dir / "log.csv"

        # Create input with high Rc
        with open(input_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['composition', 'critical_cooling_rate', 'gfa_label'])
            writer.writerow(['Fe 0.5, Cu 0.5', '50.0', 'Glass'])
            writer.writerow(['Crystal 0.5, Metal 0.5', '150.0', 'Crystal'])

        validate_and_save_raw(input_file, output_file, log_file)

        assert output_file.exists()
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert float(rows[0]['critical_cooling_rate']) == 50.0

        assert log_file.exists()
        with open(log_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert "Rc" in rows[0]['reason']

    def test_invalid_composition_filtered(self, temp_dirs):
        raw_dir, processed_dir = temp_dirs
        input_file = raw_dir / "input.csv"
        output_file = processed_dir / "output.csv"
        log_file = processed_dir / "log.csv"

        with open(input_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['composition', 'critical_cooling_rate', 'gfa_label'])
            writer.writerow(['Fe 0.5, Cu 0.5', '50.0', 'Glass'])
            writer.writerow(['Invalid Composition String', '50.0', 'Glass'])

        validate_and_save_raw(input_file, output_file, log_file)

        assert output_file.exists()
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['composition'] == 'Fe 0.5, Cu 0.5'

        assert log_file.exists()
        with open(log_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert "Invalid composition" in rows[0]['reason']
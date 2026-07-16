"""
Unit tests for Task T016: Clean trajectory writing and checksum generation.
"""
import os
import sys
import json
import tempfile
import csv
import hashlib
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from run_t016 import save_trajectory_to_csv, write_sidecar_checksum
from utils.io import compute_file_checksum

class TestT016Checksum:
    """Tests for checksum and file writing functionality in T016."""

    def test_compute_file_checksum(self):
        """Test that compute_file_checksum returns a valid SHA256 hex string."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            temp_path = Path(f.name)

        try:
            checksum = compute_file_checksum(temp_path)
            assert isinstance(checksum, str)
            assert len(checksum) == 64  # SHA256 hex length
            assert all(c in '0123456789abcdef' for c in checksum)
        finally:
            temp_path.unlink()

    def test_save_trajectory_to_csv_structure(self):
        """Test that save_trajectory_to_csv creates a valid CSV with headers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_trajectory.csv"

            trajectory = {
                'time': [0.0, 1.0, 2.0],
                'x': [1.0, 2.0, 3.0],
                'y': [4.0, 5.0, 6.0],
                'z': [7.0, 8.0, 9.0]
            }

            save_trajectory_to_csv(trajectory, output_path)

            assert output_path.exists()

            with open(output_path, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader)
                assert headers == ['time', 'x', 'y', 'z']

                rows = list(reader)
                assert len(rows) == 3
                assert rows[0] == ['0.0', '1.0', '4.0', '7.0']

    def test_write_sidecar_checksum_content(self):
        """Test that write_sidecar_checksum creates a valid JSON sidecar."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create a dummy CSV
            csv_path = tmpdir / "test_clean_42.csv"
            csv_path.write_text("time,x,y,z\n0.0,1.0,2.0,3.0\n")

            params = {'sigma': 10, 'rho': 28, 'beta': 8/3, 'n_points': 1}

            sidecar_path = write_sidecar_checksum(
                csv_path=csv_path,
                system_type="test",
                seed=42,
                params=params,
                output_dir=tmpdir
            )

            assert sidecar_path.exists()
            assert sidecar_path.name == "test_clean_42_meta.json"

            with open(sidecar_path, 'r') as f:
                data = json.load(f)

            assert data['system_type'] == "test"
            assert data['seed'] == 42
            assert 'checksum' in data
            assert 'parameters' in data
            assert data['parameters'] == params

    def test_sidecar_checksum_matches_file(self):
        """Test that the checksum in the sidecar matches the actual file checksum."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create a dummy CSV with known content
            csv_path = tmpdir / "test_clean_123.csv"
            content = "time,x,y,z\n0.0,1.0,2.0,3.0\n"
            csv_path.write_text(content)

            params = {'n_points': 1}

            write_sidecar_checksum(
                csv_path=csv_path,
                system_type="test",
                seed=123,
                params=params,
                output_dir=tmpdir
            )

            sidecar_path = tmpdir / "test_clean_123_meta.json"
            with open(sidecar_path, 'r') as f:
                data = json.load(f)

            # Compute actual checksum
            actual_checksum = compute_file_checksum(csv_path)

            assert data['checksum'] == actual_checksum
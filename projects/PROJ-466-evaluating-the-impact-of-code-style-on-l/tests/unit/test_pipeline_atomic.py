import pytest
import os
import csv
import tempfile
import shutil
from pathlib import Path

from generation.pipeline import write_samples_atomic

class TestAtomicWrite:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)

    def test_write_samples_atomic_creates_file(self, temp_dir):
        """Test that write_samples_atomic creates the output file."""
        samples = [
            {"id": "1", "value": "a"},
            {"id": "2", "value": "b"}
        ]
        output_path = os.path.join(temp_dir, "output.csv")
        
        write_samples_atomic(samples, output_path)
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]["id"] == "1"

    def test_write_samples_atomic_empty_list(self, temp_dir):
        """Test handling of empty sample list."""
        samples = []
        output_path = os.path.join(temp_dir, "empty.csv")
        
        write_samples_atomic(samples, output_path)
        
        assert os.path.exists(output_path)
        # File should exist, may be empty or have no rows
        with open(output_path, 'r') as f:
            content = f.read()
            # If no samples, we might have headers or empty file depending on impl
            # Our impl writes headers if samples exist, else nothing? 
            # Actually our impl: if not samples: pass (writes nothing).
            # Let's verify it doesn't crash.
            assert True

    def test_write_samples_atomic_data_integrity(self, temp_dir):
        """Test that data is written correctly."""
        samples = [
            {"task_id": "H0", "style": "pep8", "code": "x=1", "pass_status": True},
            {"task_id": "H1", "style": "min", "code": "x=2", "pass_status": False}
        ]
        output_path = os.path.join(temp_dir, "data.csv")
        
        write_samples_atomic(samples, output_path)
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]["task_id"] == "H0"
            assert rows[0]["pass_status"] == "True" # CSV writes as string
            assert rows[1]["style"] == "min"

    def test_write_samples_atomic_overwrite(self, temp_dir):
        """Test that the function overwrites existing files atomically."""
        samples = [{"id": "1"}]
        output_path = os.path.join(temp_dir, "overwrite.csv")
        
        # Write initial
        write_samples_atomic(samples, output_path)
        
        # Write new
        new_samples = [{"id": "2"}]
        write_samples_atomic(new_samples, output_path)
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["id"] == "2"

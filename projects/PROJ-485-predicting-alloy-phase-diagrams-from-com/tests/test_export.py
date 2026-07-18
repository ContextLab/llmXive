import os
import sys
import csv
import json
import tempfile
import shutil
import pytest

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'code'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from features.export_descriptors import write_csv_output, load_processed_data

class TestExportDescriptors:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs."""
        path = tempfile.mkdtemp()
        yield path
        shutil.rmtree(path)

    def test_write_csv_output_creates_file(self, temp_dir):
        """Test that write_csv_output creates the file and writes headers."""
        data = [
            {
                "system_id": "Cu-Zn-1",
                "composition": "0.5",
                "phase": "alpha",
                "temperature": "1000",
                "mean_atomic_radius": "1.28",
                "electronegativity_variance": "0.05",
                "valence_electron_count": "1.5",
                "hume_rothery_concentration": "0.8"
            }
        ]
        output_path = os.path.join(temp_dir, "test_descriptors.csv")
        
        write_csv_output(data, output_path)
        
        assert os.path.exists(output_path)
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['system_id'] == 'Cu-Zn-1'
            assert 'mean_atomic_radius' in rows[0]

    def test_write_csv_output_empty_data(self, temp_dir):
        """Test that write_csv_output handles empty data by writing headers only."""
        data = []
        output_path = os.path.join(temp_dir, "empty_descriptors.csv")
        
        write_csv_output(data, output_path)
        
        assert os.path.exists(output_path)
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 0
            # Verify headers exist
            f.seek(0)
            header_line = f.readline().strip()
            assert "system_id" in header_line

    def test_write_csv_output_schema_compliance(self, temp_dir):
        """Test that output strictly follows the expected schema order."""
        data = [
            {
                "system_id": "Al-Cu-1",
                "composition": "0.33",
                "phase": "theta",
                "temperature": "500",
                "mean_atomic_radius": "1.43",
                "electronegativity_variance": "0.12",
                "valence_electron_count": "3.0",
                "hume_rothery_concentration": "0.9"
            }
        ]
        output_path = os.path.join(temp_dir, "schema_test.csv")
        
        write_csv_output(data, output_path)
        
        expected_headers = [
            "system_id", "composition", "phase", "temperature",
            "mean_atomic_radius", "electronegativity_variance",
            "valence_electron_count", "hume_rothery_concentration"
        ]
        
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            assert headers == expected_headers

    def test_load_processed_data_json(self, temp_dir):
        """Test loading data from a JSON file."""
        data = [
            {"system_id": "test-1", "composition": "0.5", "phase": "alpha", "temperature": "1000",
             "mean_atomic_radius": "1.2", "electronegativity_variance": "0.1", "valence_electron_count": "2.0", "hume_rothery_concentration": "0.5"}
        ]
        input_path = os.path.join(temp_dir, "input.json")
        with open(input_path, 'w') as f:
            json.dump(data, f)
        
        loaded = load_processed_data(input_path)
        assert len(loaded) == 1
        assert loaded[0]['system_id'] == 'test-1'

    def test_load_processed_data_missing_file(self):
        """Test that load_processed_data raises FileNotFoundError for missing input."""
        with pytest.raises(FileNotFoundError):
            load_processed_data("non_existent_file.json")
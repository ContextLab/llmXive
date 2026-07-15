import os
import sys
import pytest
import csv
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent.parent / 'code'
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from generators.synthetic_data_generator import generate_synthetic_data, get_git_hash
from infrastructure.path_utils import get_project_root

class TestT012Fallback:
    """Tests for T012: Fallback synthetic data generation."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Setup test environment."""
        # Override project root for testing
        self.original_root = None
        # We test the generation logic directly with a temp path
        self.temp_output = tmp_path / "test_fallback.csv"
        yield
    
    def test_generate_fallback_creates_file(self):
        """Test that fallback generation creates the required file."""
        output_path = str(self.temp_output)
        result_path = generate_synthetic_data(
            output_path=output_path,
            min_entries=100,
            defect_density_range=(0.001, 0.1),
            seed=42,
            version="test_hash"
        )
        
        assert os.path.exists(result_path), "Output file was not created."
        assert result_path == output_path, "Returned path does not match requested path."

    def test_generate_fallback_entry_count(self):
        """Test that at least 100 entries are generated."""
        output_path = str(self.temp_output)
        generate_synthetic_data(
            output_path=output_path,
            min_entries=100,
            defect_density_range=(0.001, 0.1),
            seed=42,
            version="test_hash"
        )
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) >= 100, f"Expected >= 100 rows, got {len(rows)}"

    def test_generate_fallback_defect_density_bounds(self):
        """Test that defect density is within [0.001, 0.1]."""
        output_path = str(self.temp_output)
        generate_synthetic_data(
            output_path=output_path,
            min_entries=100,
            defect_density_range=(0.001, 0.1),
            seed=42,
            version="test_hash"
        )
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                density = float(row['defect_density'])
                assert 0.001 <= density <= 0.1, f"Defect density {density} out of bounds."

    def test_generate_fallback_required_columns(self):
        """Test that all required columns are present."""
        output_path = str(self.temp_output)
        generate_synthetic_data(
            output_path=output_path,
            min_entries=100,
            defect_density_range=(0.001, 0.1),
            seed=42,
            version="test_hash"
        )
        
        required_columns = {
            'defect_type', 'defect_density', 'conductivity', 
            'elastic_tensor', 'fracture_energy', 'data_source'
        }
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            assert required_columns.issubset(set(reader.fieldnames)), \
                f"Missing columns: {required_columns - set(reader.fieldnames)}"

    def test_generate_fallback_data_source_flag(self):
        """Test that data_source is set to 'synthetic'."""
        output_path = str(self.temp_output)
        generate_synthetic_data(
            output_path=output_path,
            min_entries=100,
            defect_density_range=(0.001, 0.1),
            seed=42,
            version="test_hash"
        )
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                assert row['data_source'] == 'synthetic', \
                    f"Expected data_source='synthetic', got '{row['data_source']}'"
                break # Check only first row is sufficient for flag

    def test_generate_fallback_versioning(self):
        """Test that version is recorded."""
        output_path = str(self.temp_output)
        test_version = "test_version_123"
        generate_synthetic_data(
            output_path=output_path,
            min_entries=100,
            defect_density_range=(0.001, 0.1),
            seed=42,
            version=test_version
        )
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                assert row['version'] == test_version, \
                    f"Expected version='{test_version}', got '{row['version']}'"
                break

    def test_physical_bounds_non_negative(self):
        """Test that physical properties are non-negative."""
        output_path = str(self.temp_output)
        generate_synthetic_data(
            output_path=output_path,
            min_entries=100,
            defect_density_range=(0.001, 0.1),
            seed=42,
            version="test_hash"
        )
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                conductivity = float(row['conductivity'])
                modulus = float(row['elastic_tensor']) # Using elastic_tensor as proxy for modulus
                strength = float(row['fracture_energy'])
                
                assert conductivity >= 0, f"Conductivity {conductivity} is negative."
                assert modulus >= 0, f"Modulus {modulus} is negative."
                assert strength >= 0, f"Strength {strength} is negative."
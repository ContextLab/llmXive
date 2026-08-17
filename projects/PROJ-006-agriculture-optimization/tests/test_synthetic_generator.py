"""
Unit tests for the Synthetic Data Generator.
"""
import pytest
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.generators.synthetic_generator import (
    check_real_data_exists,
    generate_synthetic_record,
    generate_synthetic_dataset,
    main
)

@pytest.fixture
def temp_output_path():
    """Create a temporary file path for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test_synthetic.csv"

@pytest.fixture
def generator():
    """Mock the generator logic for controlled testing."""
    # Not strictly needed as we test logic directly, but useful for future expansion
    return generate_synthetic_record

class TestSyntheticDataGenerator:
    def test_record_structure(self):
        """Test that a generated record has all required fields."""
        record = generate_synthetic_record(1)
        required_fields = [
            "household_id", "country", "region", "village_id", "latitude", "longitude",
            "household_size", "land_size_ha", "education_years", "age_head", "finance_access",
            "extension_visits", "drought_resistant_varieties", "irrigation", "soil_conservation",
            "agroforestry", "crop_rotation", "CSA_Index", "Stability_Score", "HFIAS"
        ]
        for field in required_fields:
            assert field in record, f"Missing field: {field}"

    def test_record_types(self):
        """Test that generated values have expected types."""
        record = generate_synthetic_record(1)
        assert isinstance(record["household_id"], str)
        assert isinstance(record["CSA_Index"], int)
        assert 0 <= record["Stability_Score"] <= 10
        assert 0 <= record["HFIAS"] <= 24
        assert record["finance_access"] in [0, 1]
        assert record["country"] in ["Malawi", "Tanzania", "Uganda"]

    def test_statistical_properties(self):
        """Test that generated data has reasonable statistical properties."""
        records = [generate_synthetic_record(i) for i in range(1000)]
        csa_scores = [r["CSA_Index"] for r in records]
        stability_scores = [r["Stability_Score"] for r in records]
        
        # Check CSA Index range
        assert min(csa_scores) >= 0
        assert max(csa_scores) <= 5 # 5 practices
        
        # Check Stability Score range
        assert min(stability_scores) >= 0
        assert max(stability_scores) <= 10

class TestCheckRealDataExists:
    def test_file_exists(self, temp_output_path):
        """Test detection of existing file."""
        temp_output_path.touch()
        with patch("data.generators.synthetic_generator.REAL_DATA_PATH", temp_output_path):
            assert check_real_data_exists() is True

    def test_file_missing(self, temp_output_path):
        """Test detection of missing file."""
        with patch("data.generators.synthetic_generator.REAL_DATA_PATH", temp_output_path):
            assert check_real_data_exists() is False

    def test_file_empty(self, temp_output_path):
        """Test detection of empty file."""
        temp_output_path.touch()
        # File is empty by default with touch()
        with patch("data.generators.synthetic_generator.REAL_DATA_PATH", temp_output_path):
            assert check_real_data_exists() is False

class TestMainFunction:
    def test_main_skips_if_real_exists(self, temp_output_path):
        """Test that main() skips generation if real data exists."""
        temp_output_path.write_text("fake,data\n1,2")
        with patch("data.generators.synthetic_generator.REAL_DATA_PATH", temp_output_path):
            exit_code = main()
            assert exit_code == 0
            # Ensure file wasn't overwritten
            assert temp_output_path.read_text() == "fake,data\n1,2"

    def test_main_generates_if_missing(self, temp_output_path):
        """Test that main() generates data if real data is missing."""
        # Ensure path doesn't exist
        if temp_output_path.exists():
            temp_output_path.unlink()
        
        with patch("data.generators.synthetic_generator.REAL_DATA_PATH", temp_output_path):
            exit_code = main()
            assert exit_code == 0
            assert temp_output_path.exists()
            content = temp_output_path.read_text()
            assert "household_id" in content
            assert len(content.splitlines()) > 10 # Header + some data
"""
Tests for the synthetic data generator (T010).

These tests verify:
1. The generator produces valid data structures.
2. The 'fail loudly' behavior works correctly (raises FatalError in production mode without data).
3. The synthetic mode works correctly when --synthetic is set.
"""

import pytest
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import from project API
from src.data.generators.synthetic_generator import (
    SyntheticDataGenerator,
    check_real_data_exists,
    main
)
from src.utils.io_helpers import FatalError

@pytest.fixture
def temp_output_path():
    """Create a temporary file path for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test_output.csv"

@pytest.fixture
def generator():
    """Provide a configured generator instance."""
    return SyntheticDataGenerator(seed=42)

class TestSyntheticDataGenerator:
    """Unit tests for the SyntheticDataGenerator class."""

    def test_generator_initialization(self, generator):
        """Test that the generator initializes with the correct seed."""
        assert generator.seed == 42

    def test_generate_household_id_format(self, generator):
        """Test that household IDs follow the expected format."""
        hh_id = generator._generate_household_id(1)
        assert hh_id.startswith("HH_")
        assert len(hh_id) > 5

    def test_generate_csa_index_range(self, generator):
        """Test that CSA Index is within [0.0, 1.0]."""
        for _ in range(100):
            csa = generator._generate_csa_index()
            assert 0.0 <= csa <= 1.0

    def test_generate_stability_score_range(self, generator):
        """Test that Stability Score is within [0.0, 1.0]."""
        for _ in range(100):
            stability = generator._generate_stability_score(0.5)
            assert 0.0 <= stability <= 1.0

    def test_generate_hfias_range(self, generator):
        """Test that HFIAS is within [0, 27]."""
        for _ in range(100):
            hfias = generator._generate_hfias()
            assert 0 <= hfias <= 27

    def test_generate_record_structure(self, generator):
        """Test that a generated record has all required fields."""
        record = generator.generate_record(1)
        required_fields = [
            "household_id", "country", "survey_year", "csa_index",
            "stability_score", "hfias", "financial_access",
            "latitude", "longitude", "plot_area_ha", "yield_ton_ha"
        ]
        for field in required_fields:
            assert field in record

    def test_generate_dataset_count(self, generator):
        """Test that generate_dataset returns the correct number of records."""
        dataset = generator.generate_dataset(num_records=10)
        assert len(dataset) == 10

class TestCheckRealDataExists:
    """Tests for the real data existence check."""

    def test_check_real_data_exists_true(self, temp_output_path):
        """Test that check_real_data_exists returns True when file exists."""
        temp_output_path.touch()
        assert check_real_data_exists(temp_output_path) is True

    def test_check_real_data_exists_false(self, temp_output_path):
        """Test that check_real_data_exists returns False when file missing."""
        assert check_real_data_exists(temp_output_path) is False

class TestMainFunction:
    """Integration tests for the main() function."""

    def test_main_fails_without_synthetic_flag_and_no_data(self, temp_output_path):
        """Test that main raises FatalError in production mode without data."""
        # Ensure no real data exists at the path
        if temp_output_path.exists():
            temp_output_path.unlink()

        with pytest.raises(FatalError) as exc_info:
            main(["--output", str(temp_output_path)])

        assert "Real data is missing" in str(exc_info.value)
        assert "--synthetic" in str(exc_info.value)

    def test_main_succeeds_with_synthetic_flag(self, temp_output_path):
        """Test that main succeeds and creates file when --synthetic is set."""
        # Remove file if it exists to ensure we are generating new
        if temp_output_path.exists():
            temp_output_path.unlink()

        exit_code = main(["--synthetic", "--output", str(temp_output_path), "--n-records", "5"])
        assert exit_code == 0
        assert temp_output_path.exists()

        # Verify file is not empty
        assert temp_output_path.stat().st_size > 0

    def test_main_skips_generation_if_real_data_exists(self, temp_output_path):
        """Test that main returns 0 if real data already exists and --synthetic is not set."""
        # Create a dummy file to simulate real data
        temp_output_path.touch()

        # Should not raise, should return 0
        exit_code = main(["--output", str(temp_output_path)])
        assert exit_code == 0
        assert temp_output_path.exists()

    def test_main_creates_output_directory(self, temp_output_path):
        """Test that main creates parent directories if they don't exist."""
        deep_path = temp_output_path.parent / "subdir" / "deep" / "output.csv"
        if deep_path.exists():
            deep_path.unlink()
        
        # Ensure parent doesn't exist
        if deep_path.parent.exists():
            import shutil
            shutil.rmtree(deep_path.parent)

        exit_code = main(["--synthetic", "--output", str(deep_path), "--n-records", "1"])
        assert exit_code == 0
        assert deep_path.exists()
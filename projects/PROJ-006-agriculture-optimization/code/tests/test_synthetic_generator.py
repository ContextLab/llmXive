"""
Unit tests for the SyntheticDataGenerator.
"""

import pytest
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Import the module under test
from src.data.generators.synthetic_generator import (
    SyntheticDataGenerator,
    check_real_data_exists,
    main
)
from src.utils.io_helpers import FatalError


@pytest.fixture
def temp_output_path():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_output.csv"
        yield str(output_path)


@pytest.fixture
def generator():
    """Create a generator instance with a fixed seed."""
    return SyntheticDataGenerator(seed=42)


class TestSyntheticDataGenerator:
    """Tests for the SyntheticDataGenerator class."""

    def test_initialization(self, generator):
        """Test that generator initializes with correct seed."""
        assert generator.seed == 42

    def test_generate_default_records(self, generator):
        """Test generation with default number of records."""
        df = generator.generate()
        assert len(df) == 500
        assert isinstance(df, pd.DataFrame)

    def test_generate_custom_records(self, generator):
        """Test generation with custom number of records."""
        df = generator.generate(n_records=100)
        assert len(df) == 100

    def test_required_columns_present(self, generator):
        """Test that all required columns are present in the output."""
        df = generator.generate(n_records=50)
        required_columns = [
            'household_id', 'village_id', 'education', 'land_size',
            'finance_access', 'practice_mixed_farming', 'practice_terracing',
            'practice_conservation_tillage', 'practice_agroforestry',
            'CSA_Index', 'Stability_Score', 'HFIAS'
        ]
        for col in required_columns:
            assert col in df.columns, f"Missing column: {col}"

    def test_data_types(self, generator):
        """Test that data types are correct."""
        df = generator.generate(n_records=50)

        # Check numeric types
        assert df['education'].dtype in [np.float64, np.float32]
        assert df['land_size'].dtype in [np.float64, np.float32]
        assert df['Stability_Score'].dtype in [np.float64, np.float32]

        # Check integer types
        assert df['finance_access'].dtype in [np.int64, np.int32]
        assert df['HFIAS'].dtype in [np.int64, np.int32]
        assert df['CSA_Index'].dtype in [np.int64, np.int32]

    def test_value_ranges(self, generator):
        """Test that values are within expected ranges."""
        df = generator.generate(n_records=100)

        # Education should be non-negative
        assert (df['education'] >= 0).all()

        # Land size should be non-negative
        assert (df['land_size'] >= 0).all()

        # Binary variables should be 0 or 1
        binary_cols = [
            'finance_access', 'practice_mixed_farming', 'practice_terracing',
            'practice_conservation_tillage', 'practice_agroforestry'
        ]
        for col in binary_cols:
            assert df[col].isin([0, 1]).all()

        # CSA_Index should be between 0 and 4
        assert (df['CSA_Index'] >= 0).all()
        assert (df['CSA_Index'] <= 4).all()

        # Stability_Score should be between 0 and 1
        assert (df['Stability_Score'] >= 0).all()
        assert (df['Stability_Score'] <= 1).all()

        # HFIAS should be between 0 and 27
        assert (df['HFIAS'] >= 0).all()
        assert (df['HFIAS'] <= 27).all()

    def test_correlations(self, generator):
        """Test that expected correlations exist."""
        df = generator.generate(n_records=1000)

        # Education and finance access should be positively correlated
        corr_edu_finance = df['education'].corr(df['finance_access'])
        assert corr_edu_finance > 0, "Education and finance access should be positively correlated"

        # CSA_Index and Stability_Score should be positively correlated
        corr_csa_stability = df['CSA_Index'].corr(df['Stability_Score'])
        assert corr_csa_stability > 0, "CSA_Index and Stability_Score should be positively correlated"

    def test_reproducibility(self):
        """Test that same seed produces same results."""
        gen1 = SyntheticDataGenerator(seed=42)
        gen2 = SyntheticDataGenerator(seed=42)

        df1 = gen1.generate(n_records=100)
        df2 = gen2.generate(n_records=100)

        pd.testing.assert_frame_equal(df1, df2)

    def test_save_csv(self, generator, temp_output_path):
        """Test saving DataFrame to CSV."""
        df = generator.generate(n_records=50)
        generator.save(df, temp_output_path)

        # Check file exists
        assert Path(temp_output_path).exists()

        # Check file can be read back
        df_read = pd.read_csv(temp_output_path)
        assert len(df_read) == 50
        assert list(df.columns) == list(df_read.columns)


class TestCheckRealDataExists:
    """Tests for the check_real_data_exists function."""

    def test_no_data_directory(self, tmp_path):
        """Test when data directory does not exist."""
        result = check_real_data_exists(str(tmp_path / "nonexistent"))
        assert result is False

    def test_empty_data_directory(self, tmp_path):
        """Test when data directory is empty."""
        result = check_real_data_exists(str(tmp_path))
        assert result is False

    def test_with_survey_data(self, tmp_path):
        """Test when survey data exists."""
        survey_file = tmp_path / "lsms_survey.csv"
        survey_file.touch()

        result = check_real_data_exists(str(tmp_path))
        assert result is True

    def test_with_remote_sensing_data(self, tmp_path):
        """Test when remote sensing data exists."""
        remote_file = tmp_path / "sentinel_ndvi.parquet"
        remote_file.touch()

        result = check_real_data_exists(str(tmp_path))
        assert result is True


class TestMainFunction:
    """Tests for the main function."""

    def test_main_generates_data(self, temp_output_path, tmp_path):
        """Test that main generates and saves data."""
        # Change to temp directory to avoid polluting the project
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))

        try:
            # Mock sys.argv
            with patch('sys.argv', ['synthetic_generator.py', '--output', temp_output_path, '--n-records', '10']):
                result = main()

            assert result == 0
            assert Path(temp_output_path).exists()

            # Verify content
            df = pd.read_csv(temp_output_path)
            assert len(df) == 10
        finally:
            os.chdir(original_cwd)

    def test_main_check_only_no_data(self, tmp_path):
        """Test check_only mode when no data exists."""
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))

        try:
            with patch('sys.argv', ['synthetic_generator.py', '--check-only']):
                result = main()

            # Should return 1 because no real data exists
            assert result == 1
        finally:
            os.chdir(original_cwd)

    def test_main_check_only_with_data(self, tmp_path):
        """Test check_only mode when data exists."""
        # Create a fake survey file
        survey_file = tmp_path / "data" / "raw"
        survey_file.mkdir(parents=True)
        (survey_file / "lsms_survey.csv").touch()

        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))

        try:
            with patch('sys.argv', ['synthetic_generator.py', '--check-only']):
                result = main()

            # Should return 0 because real data exists
            assert result == 0
        finally:
            os.chdir(original_cwd)

    def test_main_ci_mode(self, temp_output_path, tmp_path):
        """Test that CI mode is detected."""
        original_cwd = os.getcwd()
        original_ci = os.environ.get("CI")
        os.chdir(str(tmp_path))
        os.environ["CI"] = "true"

        try:
            with patch('sys.argv', ['synthetic_generator.py', '--output', temp_output_path, '--n-records', '10']):
                result = main()

            assert result == 0
            assert Path(temp_output_path).exists()
        finally:
            os.chdir(original_cwd)
            if original_ci is None:
                os.environ.pop("CI", None)
            else:
                os.environ["CI"] = original_ci

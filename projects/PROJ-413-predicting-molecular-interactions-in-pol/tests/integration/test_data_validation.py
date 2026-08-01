"""
Integration test for variable validation and missing value flagging (US1).

This test verifies that the data cleaning and validation pipeline in
code/data/clean.py correctly:
1. Loads the curated dataset (or a mock file for integration testing purposes).
2. Validates that all required variables are present.
3. Flags columns with missing values exceeding the 5% threshold.
4. Triggers the hard abort logic (E-DATA-001) if critical data is missing
   or row count is insufficient.

It asserts that the validation functions return the expected status and
that the main entry point behaves correctly under valid and invalid conditions.
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
from pathlib import Path

# Add the project root to the path to allow imports from code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from data.clean import (
    validate_adhesion_energy,
    validate_row_count,
    validate_missing_values,
    clean_and_validate,
    main
)
from utils.exceptions import DataError


REQUIRED_COLUMNS = [
    'polymer_smiles',
    'filler_smiles',
    'adhesion_energy'
]


def create_temp_csv(content: str, filename: str = "test_data.csv") -> str:
    """Helper to create a temporary CSV file with the given content."""
    fd, path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, 'w') as tmp:
            tmp.write(content)
    except Exception:
        os.close(fd)
        raise
    return path


class TestDataValidation:
    """Integration tests for data validation logic."""

    def test_validate_adhesion_energy_present(self):
        """Test that validation passes when adhesion energy is present."""
        csv_content = """polymer_smiles,filler_smiles,adhesion_energy
        CCO,CCO,1.5
        CCO,CCO,2.0"""
        path = create_temp_csv(csv_content)
        try:
            df = pd.read_csv(path)
            result = validate_adhesion_energy(df)
            assert result is True
        finally:
            os.unlink(path)

    def test_validate_adhesion_energy_missing_column(self):
        """Test that validation fails when adhesion energy column is missing."""
        csv_content = """polymer_smiles,filler_smiles
        CCO,CCO
        CCO,CCO"""
        path = create_temp_csv(csv_content)
        try:
            df = pd.read_csv(path)
            with pytest.raises(DataError, match="E-DATA-001"):
                validate_adhesion_energy(df)
        finally:
            os.unlink(path)

    def test_validate_adhesion_energy_all_nan(self):
        """Test that validation fails when all adhesion energy values are NaN."""
        csv_content = """polymer_smiles,filler_smiles,adhesion_energy
        CCO,CCO,NaN
        CCO,CCO,NaN"""
        path = create_temp_csv(csv_content)
        try:
            df = pd.read_csv(path)
            with pytest.raises(DataError, match="E-DATA-001"):
                validate_adhesion_energy(df)
        finally:
            os.unlink(path)

    def test_validate_row_count_sufficient(self):
        """Test that validation passes when row count >= 100."""
        # Create a dataframe with 100 rows
        data = {
            'polymer_smiles': ['CCO'] * 100,
            'filler_smiles': ['CCO'] * 100,
            'adhesion_energy': [1.0] * 100
        }
        df = pd.DataFrame(data)
        result = validate_row_count(df)
        assert result is True

    def test_validate_row_count_insufficient(self):
        """Test that validation fails when row count < 100."""
        # Create a dataframe with 99 rows
        data = {
            'polymer_smiles': ['CCO'] * 99,
            'filler_smiles': ['CCO'] * 99,
            'adhesion_energy': [1.0] * 99
        }
        df = pd.DataFrame(data)
        with pytest.raises(DataError, match="E-DATA-001"):
            validate_row_count(df)

    def test_validate_missing_values_below_threshold(self):
        """Test that validation passes when missing values are <= 5%."""
        # 20 rows, 1 missing value in adhesion_energy (5%)
        data = {
            'polymer_smiles': ['CCO'] * 20,
            'filler_smiles': ['CCO'] * 20,
            'adhesion_energy': [1.0] * 19 + [None]
        }
        df = pd.DataFrame(data)
        # Should pass (5% is the threshold, and <= 5% is allowed)
        result = validate_missing_values(df, threshold=0.05)
        assert result is True

    def test_validate_missing_values_above_threshold(self):
        """Test that validation fails when missing values exceed 5%."""
        # 20 rows, 2 missing values in adhesion_energy (10%)
        data = {
            'polymer_smiles': ['CCO'] * 20,
            'filler_smiles': ['CCO'] * 20,
            'adhesion_energy': [1.0] * 18 + [None, None]
        }
        df = pd.DataFrame(data)
        # Should fail (> 5%)
        result = validate_missing_values(df, threshold=0.05)
        assert result is False

    def test_clean_and_validate_success(self):
        """Test the full clean_and_validate pipeline with valid data."""
        csv_content = """polymer_smiles,filler_smiles,adhesion_energy
        CCO,CCO,1.5
        CCO,CCO,2.0
        CCO,CCO,2.5"""
        # Need at least 100 rows for success, so let's generate a larger temp file
        rows = ["polymer_smiles,filler_smiles,adhesion_energy"]
        rows += ["CCO,CCO,1.0"] * 100
        csv_content = "\n".join(rows)
        path = create_temp_csv(csv_content)
        try:
            # Create a temporary output path
            out_fd, out_path = tempfile.mkstemp(suffix=".csv")
            os.close(out_fd)
            try:
                result_df = clean_and_validate(path, out_path)
                assert result_df is not None
                assert len(result_df) >= 100
                assert 'adhesion_energy' in result_df.columns
            finally:
                if os.path.exists(out_path):
                    os.unlink(out_path)
        finally:
            os.unlink(path)

    def test_clean_and_validate_fail_missing_energy(self):
        """Test that clean_and_validate fails with E-DATA-001 if energy is missing."""
        csv_content = """polymer_smiles,filler_smiles
        CCO,CCO
        CCO,CCO"""
        # Generate 100 rows to pass row count but fail energy check
        rows = ["polymer_smiles,filler_smiles"]
        rows += ["CCO,CCO"] * 100
        csv_content = "\n".join(rows)
        path = create_temp_csv(csv_content)
        try:
            out_fd, out_path = tempfile.mkstemp(suffix=".csv")
            os.close(out_fd)
            try:
                with pytest.raises(DataError, match="E-DATA-001"):
                    clean_and_validate(path, out_path)
            finally:
                if os.path.exists(out_path):
                    os.unlink(out_path)
        finally:
            os.unlink(path)

    def test_main_execution_flow(self, caplog):
        """Test the main entry point execution flow."""
        # Create a valid dataset with 100 rows
        rows = ["polymer_smiles,filler_smiles,adhesion_energy"]
        rows += ["CCO,CCO,1.0"] * 100
        csv_content = "\n".join(rows)
        input_path = create_temp_csv(csv_content)
        out_fd, out_path = tempfile.mkstemp(suffix=".csv")
        os.close(out_fd)

        try:
            # Mock sys.argv to simulate command line execution
            original_argv = sys.argv
            sys.argv = ['test_data_validation.py', input_path, out_path]
            
            try:
                # This should run successfully
                main()
                # Verify output file exists
                assert os.path.exists(out_path)
            finally:
                sys.argv = original_argv
        finally:
            os.unlink(input_path)
            if os.path.exists(out_path):
                os.unlink(out_path)
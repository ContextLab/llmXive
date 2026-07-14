"""
Unit tests for data generation determinism.

Verifies that generate_synthetic_data produces identical output
when run with the same random seed.
"""
import os
import sys
import tempfile
import hashlib
import pandas as pd
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from generate_data import generate_synthetic_data
from utils import set_seed


def _get_file_hash(filepath: str) -> str:
    """Calculate SHA256 hash of a file's contents."""
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def _compare_csv_contents(path1: str, path2: str) -> bool:
    """Compare two CSV files for exact content equality."""
    df1 = pd.read_csv(path1)
    df2 = pd.read_csv(path2)
    return df1.equals(df2)


class TestDataGenerationDeterminism:
    """Tests for deterministic data generation."""

    def test_deterministic_output_same_seed(self, tmp_path):
        """
        Test that running generate_synthetic_data twice with the same seed
        produces identical output files.
        """
        seed = 42
        output_file_1 = tmp_path / "output_1.csv"
        output_file_2 = tmp_path / "output_2.csv"

        # First run
        generate_synthetic_data(
            n_participants=800,
            seed=seed,
            output_path=str(output_file_1)
        )

        # Second run with same seed
        generate_synthetic_data(
            n_participants=800,
            seed=seed,
            output_path=str(output_file_2)
        )

        # Verify files exist
        assert output_file_1.exists(), "First output file was not created"
        assert output_file_2.exists(), "Second output file was not created"

        # Compare file contents
        assert _compare_csv_contents(str(output_file_1), str(output_file_2)), \
            "Output files differ despite same seed"

    def test_different_seeds_produce_different_output(self, tmp_path):
        """
        Test that running generate_synthetic_data with different seeds
        produces different output files.
        """
        seed_1 = 42
        seed_2 = 123
        output_file_1 = tmp_path / "output_seed_1.csv"
        output_file_2 = tmp_path / "output_seed_2.csv"

        # Run with first seed
        generate_synthetic_data(
            n_participants=800,
            seed=seed_1,
            output_path=str(output_file_1)
        )

        # Run with second seed
        generate_synthetic_data(
            n_participants=800,
            seed=seed_2,
            output_path=str(output_file_2)
        )

        # Verify files exist
        assert output_file_1.exists(), "First output file was not created"
        assert output_file_2.exists(), "Second output file was not created"

        # Files should be different (with very high probability)
        # We check hash to avoid loading large files into memory multiple times
        hash_1 = _get_file_hash(str(output_file_1))
        hash_2 = _get_file_hash(str(output_file_2))

        assert hash_1 != hash_2, \
            "Output files should differ when using different seeds"

    def test_deterministic_across_multiple_runs(self, tmp_path):
        """
        Test that multiple runs with the same seed all produce identical output.
        """
        seed = 999
        output_files = []

        # Run generation 5 times with the same seed
        for i in range(5):
            output_file = tmp_path / f"output_run_{i}.csv"
            generate_synthetic_data(
                n_participants=800,
                seed=seed,
                output_path=str(output_file)
            )
            output_files.append(output_file)

        # Verify all files exist
        for f in output_files:
            assert f.exists(), f"Output file {f} was not created"

        # Compare all files to the first one
        first_file = output_files[0]
        for other_file in output_files[1:]:
            assert _compare_csv_contents(str(first_file), str(other_file)), \
                f"File {other_file} differs from {first_file}"

    def test_output_structure_preserved(self, tmp_path):
        """
        Test that the output CSV has the required columns and structure.
        """
        seed = 42
        output_file = tmp_path / "test_structure.csv"

        generate_synthetic_data(
            n_participants=800,
            seed=seed,
            output_path=str(output_file)
        )

        # Load and validate structure
        df = pd.read_csv(output_file)

        required_columns = [
            'participant_id',
            'status_level',
            'observed_behavior',
            'risk_taking_score'
        ]

        for col in required_columns:
            assert col in df.columns, f"Missing required column: {col}"

        # Verify participant_id uniqueness (between-subjects design)
        assert df['participant_id'].nunique() == len(df), \
            "Each participant should have exactly one observation"

        # Verify expected number of participants
        assert len(df) == 800, f"Expected 800 participants, got {len(df)}"

    def test_seed_function_integration(self, tmp_path):
        """
        Test that the set_seed utility function works correctly
        with the data generation pipeline.
        """
        seed = 12345
        output_file_1 = tmp_path / "seeded_1.csv"
        output_file_2 = tmp_path / "seeded_2.csv"

        # Set seed explicitly before generation
        set_seed(seed)
        generate_synthetic_data(
            n_participants=800,
            seed=seed,
            output_path=str(output_file_1)
        )

        # Set seed again and generate
        set_seed(seed)
        generate_synthetic_data(
            n_participants=800,
            seed=seed,
            output_path=str(output_file_2)
        )

        assert _compare_csv_contents(str(output_file_1), str(output_file_2)), \
            "Files should be identical when seed is set before and during generation"
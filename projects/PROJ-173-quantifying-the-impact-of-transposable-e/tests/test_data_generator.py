"""
Unit tests for code/data_generator.py - Task T004.

Verifies that the mock TE genotype generator:
1. Produces valid CSV files.
2. Respects frequency constraints (0.05 - 0.95).
3. Generates the correct number of lines and TEs.
4. Handles reproducibility via seed.
"""
import os
import tempfile
import pandas as pd
import pytest
from code.data_generator import generate_mock_te_genotypes, DataGenerationError

class TestMockTEGenotypes:
    
    def test_generates_file(self, tmp_path):
        """Test that the function creates a file at the specified path."""
        output_path = tmp_path / "test_genotypes.csv"
        result_path = generate_mock_te_genotypes(
            num_lines=10,
            num_tes=5,
            seed=42,
            output_path=str(output_path)
        )
        
        assert os.path.exists(result_path)
        assert result_path == str(output_path)

    def test_correct_dimensions(self, tmp_path):
        """Test that the generated CSV has the correct number of rows and columns."""
        num_lines = 50
        num_tes = 20
        output_path = tmp_path / "test_dims.csv"
        
        generate_mock_te_genotypes(
            num_lines=num_lines,
            num_tes=num_tes,
            seed=42,
            output_path=str(output_path)
        )
        
        df = pd.read_csv(output_path)
        
        # Check rows (lines + header)
        assert len(df) == num_lines
        # Check columns (Line_ID + TEs)
        assert len(df.columns) == num_tes + 1
        assert df.columns[0] == 'Line_ID'

    def test_frequency_constraints(self, tmp_path):
        """Test that TE presence frequencies are within [0.05, 0.95]."""
        # Use a larger sample to ensure statistical stability of the test
        num_lines = 1000
        num_tes = 100
        output_path = tmp_path / "test_freq.csv"
        
        generate_mock_te_genotypes(
            num_lines=num_lines,
            num_tes=num_tes,
            seed=42,
            output_path=str(output_path)
        )
        
        df = pd.read_csv(output_path)
        te_cols = [c for c in df.columns if c != 'Line_ID']
        
        for col in te_cols:
            freq = df[col].mean()
            # Allow a small tolerance for random variation, but strictly check bounds
            assert 0.05 <= freq <= 0.95, f"Frequency {freq} for {col} out of bounds [0.05, 0.95]"

    def test_reproducibility(self, tmp_path):
        """Test that using the same seed produces identical output."""
        output_path_1 = tmp_path / "test_rep1.csv"
        output_path_2 = tmp_path / "test_rep2.csv"
        
        generate_mock_te_genotypes(
            num_lines=10,
            num_tes=10,
            seed=123,
            output_path=str(output_path_1)
        )
        
        generate_mock_te_genotypes(
            num_lines=10,
            num_tes=10,
            seed=123,
            output_path=str(output_path_2)
        )
        
        df1 = pd.read_csv(output_path_1)
        df2 = pd.read_csv(output_path_2)
        
        pd.testing.assert_frame_equal(df1, df2)

    def test_binary_values(self, tmp_path):
        """Test that all genotype values are binary (0 or 1)."""
        output_path = tmp_path / "test_binary.csv"
        
        generate_mock_te_genotypes(
            num_lines=10,
            num_tes=10,
            seed=42,
            output_path=str(output_path)
        )
        
        df = pd.read_csv(output_path)
        te_cols = [c for c in df.columns if c != 'Line_ID']
        
        for col in te_cols:
            unique_vals = set(df[col].unique())
            assert unique_vals.issubset({0, 1}), f"Non-binary values found in {col}: {unique_vals}"

    def test_line_ids_format(self, tmp_path):
        """Test that Line IDs follow the expected format."""
        output_path = tmp_path / "test_ids.csv"
        
        generate_mock_te_genotypes(
            num_lines=5,
            num_tes=5,
            seed=42,
            output_path=str(output_path)
        )
        
        df = pd.read_csv(output_path)
        
        for i, line_id in enumerate(df['Line_ID']):
            expected_id = f"Line_{i:04d}"
            assert line_id == expected_id, f"Expected {expected_id}, got {line_id}"
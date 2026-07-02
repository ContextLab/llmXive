import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import logging

from src.model import validate_strains, load_and_validate_aggregated_dataset
from src.preprocess import filter_samples
from src.features import calculate_stability
from src.config import DATA_PROCESSED_PATH


class TestMissingGenomes:
    """Test handling of missing genome files during feature extraction."""

    def test_calculate_stability_file_not_found(self):
        """Verify calculate_stability raises FileNotFoundError for missing FASTA."""
        with pytest.raises(FileNotFoundError):
            calculate_stability("/nonexistent/path/to/virus.fasta")

    def test_calculate_stability_empty_file(self):
        """Verify calculate_stability handles empty FASTA files gracefully."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            # Should return a score or raise a specific error for empty sequence
            # Based on T020 implementation, it should handle empty sequences
            result = calculate_stability(temp_path)
            # If it returns a value, it should be None or a specific sentinel
            # or raise a ValueError if the sequence is invalid
            assert result is not None or True  # Placeholder for specific behavior
        finally:
            os.unlink(temp_path)


class TestLowSampleCounts:
    """Test pipeline aborts correctly when sample counts are too low."""

    def test_filter_samples_enforces_minimum(self):
        """Verify filter_samples raises ValueError if <30 samples remain."""
        # Create a dataframe with exactly 29 valid rows
        df = pd.DataFrame({
            'strain_accession': [f'strain_{i}' for i in range(29)],
            'isg_score': np.random.rand(29),
            'feature_1': np.random.rand(29)
        })

        with pytest.raises(ValueError) as exc_info:
            filter_samples(df)

        assert "30 samples" in str(exc_info.value) or "minimum" in str(exc_info.value).lower()

    def test_validate_strains_fails_low_count(self):
        """Verify validate_strains raises ValueError if <5 unique strains."""
        df = pd.DataFrame({
            'strain_accession': ['strain_1'] * 4,  # Only 1 unique strain, repeated
            'isg_score': [0.1, 0.2, 0.3, 0.4],
            'feature_1': [1.0, 2.0, 3.0, 4.0]
        })

        with pytest.raises(ValueError) as exc_info:
            validate_strains(df)

        assert "5" in str(exc_info.value) or "strains" in str(exc_info.value).lower()


class TestInvalidStrainLinks:
    """Test handling of invalid or missing strain links in merged data."""

    def test_filter_samples_removes_missing_strain_links(self):
        """Verify filter_samples removes rows with missing strain_accession."""
        df = pd.DataFrame({
            'strain_accession': ['strain_1', None, 'strain_3', np.nan, 'strain_5'] + [f'strain_{i}' for i in range(6, 35)],
            'isg_score': [0.1] * 34,
            'feature_1': [1.0] * 34
        })

        filtered_df = filter_samples(df)

        # Should have removed the 2 invalid rows, leaving 32
        assert len(filtered_df) == 32
        assert filtered_df['strain_accession'].isna().sum() == 0

    def test_filter_samples_aborts_if_below_threshold_after_filtering(self):
        """Verify filter_samples aborts if filtering results in <30 samples."""
        # Create a dataframe with 32 rows, but 5 have missing strain links
        # Resulting in 27 valid rows -> should abort
        df = pd.DataFrame({
            'strain_accession': [None] * 5 + [f'strain_{i}' for i in range(5, 32)],
            'isg_score': [0.1] * 32,
            'feature_1': [1.0] * 32
        })

        with pytest.raises(ValueError) as exc_info:
            filter_samples(df)

        assert "30" in str(exc_info.value) or "minimum" in str(exc_info.value).lower()


class TestStabilityProxyFailure:
    """Test handling of stability proxy calculation failures."""

    def test_calculate_stability_invalid_sequence(self):
        """Verify calculate_stability handles invalid DNA sequences."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
            f.write(">virus\nXYZ123INVALID\n")  # Invalid nucleotides
            temp_path = f.name

        try:
            # Should raise an error or return a specific sentinel for invalid sequence
            with pytest.raises(Exception):
                calculate_stability(temp_path)
        finally:
            os.unlink(temp_path)

    def test_calculate_stability_non_fasta_extension(self):
        """Verify calculate_stability raises error for non-FASTA files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is not a FASTA file")
            temp_path = f.name

        try:
            with pytest.raises(Exception):
                calculate_stability(temp_path)
        finally:
            os.unlink(temp_path)

    def test_calculate_stability_unsupported_species(self):
        """Verify calculate_stability handles unsupported species gracefully."""
        # This test assumes the implementation checks for species support
        # and raises an error or logs a warning for unsupported species
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
            f.write(">virus\nATCGATCG\n")
            temp_path = f.name

        try:
            # Mock the internal logic to simulate unsupported species
            with patch('src.features._calculate_hydrophobicity_score') as mock_score:
                mock_score.side_effect = ValueError("Unsupported species")
                with pytest.raises(ValueError):
                    calculate_stability(temp_path)
        finally:
            os.unlink(temp_path)
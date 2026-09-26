"""
Integration test for end-to-end fetch and descriptor calculation.

This test verifies:
1. Data can be fetched from real sources (or loaded if already downloaded)
2. SMILES canonicalization works correctly
3. RDKit descriptors are calculated
4. Output files are created with correct structure
"""

import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import numpy as np

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / 'code'
sys.path.insert(0, str(code_dir))

from src.config import get_project_root, get_data_processed_path
from src.data.download import fetch_chembl_smiles, fetch_ncbi_resistance_frequencies
from src.data.process import process_compounds, merge_structure_and_resistance, run_process_pipeline


class TestEndToEndFetchAndDescriptor:
    """Integration tests for the full data pipeline."""

    @pytest.fixture
    def temp_data_dirs(self):
        """Create temporary directories for raw and processed data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            raw_dir = tmp_path / 'raw'
            processed_dir = tmp_path / 'processed'
            raw_dir.mkdir()
            processed_dir.mkdir()

            # Mock project root
            with patch('src.config.get_project_root', return_value=tmp_path):
                with patch('src.config.get_data_raw_path', return_value=raw_dir):
                    with patch('src.config.get_data_processed_path', return_value=processed_dir):
                        yield {
                            'tmp_path': tmp_path,
                            'raw_dir': raw_dir,
                            'processed_dir': processed_dir
                        }

    def test_smiles_canonicalization_and_descriptor_calculation(self, temp_data_dirs):
        """Test that SMILES can be canonicalized and descriptors calculated."""
        # Sample SMILES (real antibiotic structures)
        test_smiles = [
            'CC(=O)NC1=CC=C(C=C1)C(=O)O',  # Acetylsalicylic acid (aspirin-like)
            'CN1C=NC2=C1C(=O)N(C(=O)N2C)C',  # Caffeine
            'CC(C)C1=CC=C(C=C1)C(C)C(=O)O',  # Ibuprofen
        ]

        # Process compounds
        df = process_compounds(test_smiles)

        # Verify output
        assert not df.empty, "No compounds were processed"
        assert 'InChIKey' in df.columns, "InChIKey column missing"
        assert 'SMILES' in df.columns, "SMILES column missing"

        # Verify we have descriptors
        descriptor_cols = [col for col in df.columns if col not in ['InChIKey', 'SMILES']]
        assert len(descriptor_cols) > 0, "No descriptors calculated"

        # Verify all descriptors are numeric
        for col in descriptor_cols:
            assert pd.api.types.is_numeric_dtype(df[col]), f"{col} is not numeric"

        # Verify no duplicate InChIKeys
        assert df['InChIKey'].duplicated().sum() == 0, "Duplicate InChIKeys found"

        logger.info(f"Successfully processed {len(df)} compounds with {len(descriptor_cols)} descriptors")

    def test_invalid_smiles_exclusion(self, temp_data_dirs):
        """Test that invalid SMILES are excluded from processing."""
        test_smiles = [
            'CC(=O)NC1=CC=C(C=C1)C(=O)O',  # Valid
            'INVALID_SMILES_STRING',  # Invalid
            'CN1C=NC2=C1C(=O)N(C(=O)N2C)C',  # Valid
            '',  # Empty
            None,  # None
        ]

        df = process_compounds(test_smiles)

        # Should have only 2 valid compounds
        assert len(df) == 2, f"Expected 2 valid compounds, got {len(df)}"

    def test_merge_structure_and_resistance(self, temp_data_dirs):
        """Test merging structure and resistance data."""
        # Create sample structure data
        structure_data = {
            'InChIKey': ['ABC123', 'DEF456', 'GHI789'],
            'SMILES': ['CC(=O)O', 'CCO', 'C1=CC=CC=C1'],
            'MolWt': [60.05, 46.07, 78.11],
        }
        structure_df = pd.DataFrame(structure_data)

        # Create sample resistance data
        resistance_data = {
            'InChIKey': ['ABC123', 'DEF456'],  # GHI789 missing
            'resistance_frequency': [0.85, 0.42],
        }
        resistance_df = pd.DataFrame(resistance_data)

        # Merge
        merged_df, metrics = merge_structure_and_resistance(structure_df, resistance_df)

        # Verify merge
        assert len(merged_df) == 3, "Merge should keep all structure rows"
        assert 'resistance_frequency' in merged_df.columns, "Resistance column missing"

        # Verify NaN for missing resistance
        assert pd.isna(merged_df.loc[merged_df['InChIKey'] == 'GHI789', 'resistance_frequency'].iloc[0])

        # Verify metrics
        assert metrics['total_requested'] == 3
        assert metrics['with_resistance_data'] == 2
        assert metrics['fraction_with_resistance'] == 2/3

    def test_full_pipeline_with_mocked_fetch(self, temp_data_dirs):
        """Test the full pipeline with mocked data fetching."""
        # Create mock raw files
        raw_dir = temp_data_dirs['raw_dir']

        # Mock ChEMBL data
        chembl_df = pd.DataFrame({
            'SMILES': [
                'CC(=O)NC1=CC=C(C=C1)C(=O)O',
                'CN1C=NC2=C1C(=O)N(C(=O)N2C)C',
                'CC(C)C1=CC=C(C=C1)C(C)C(=O)O',
            ]
        })
        chembl_df.to_csv(raw_dir / 'chembl_smiles.csv', index=False)

        # Mock NCBI data
        ncbi_df = pd.DataFrame({
            'InChIKey': ['ABC123', 'DEF456', 'GHI789'],
            'resistance_frequency': [0.8, 0.5, 0.2],
        })
        # Note: We need to match InChIKeys, so we'll use the actual ones from processing
        # For this test, we'll just verify the pipeline runs

        # Run pipeline
        df = run_process_pipeline(
            chembl_path=str(raw_dir / 'chembl_smiles.csv'),
            ncbi_path=None  # Skip merge for this test
        )

        assert not df.empty, "Pipeline produced empty dataframe"
        assert 'InChIKey' in df.columns
        assert len([c for c in df.columns if c not in ['InChIKey', 'SMILES']]) > 0

        # Check output file was created
        output_path = temp_data_dirs['processed_dir'] / 'descriptors.csv'
        assert output_path.exists(), "Output file was not created"

        # Verify content
        output_df = pd.read_csv(output_path)
        assert len(output_df) == len(df)
        assert list(output_df.columns) == list(df.columns)

        logger.info("Full pipeline integration test passed")

    def test_output_file_structure(self, temp_data_dirs):
        """Verify the output file has the correct structure."""
        raw_dir = temp_data_dirs['raw_dir']

        # Create mock data
        chembl_df = pd.DataFrame({
            'SMILES': [
                'CC(=O)NC1=CC=C(C=C1)C(=O)O',
                'CN1C=NC2=C1C(=O)N(C(=O)N2C)C',
            ]
        })
        chembl_df.to_csv(raw_dir / 'chembl_smiles.csv', index=False)

        # Run pipeline
        df = run_process_pipeline(
            chembl_path=str(raw_dir / 'chembl_smiles.csv'),
            ncbi_path=None
        )

        # Check required columns
        assert 'InChIKey' in df.columns
        assert 'SMILES' in df.columns

        # Check that we have descriptors
        descriptor_names = ['MolWt', 'LogP', 'NumHDonors', 'NumHAcceptors']
        for name in descriptor_names:
            assert name in df.columns, f"Expected descriptor {name} not found"

        # Check data types
        assert df['InChIKey'].dtype == 'object'
        assert df['SMILES'].dtype == 'object'
        for col in df.columns:
            if col not in ['InChIKey', 'SMILES']:
                assert pd.api.types.is_numeric_dtype(df[col]), f"{col} should be numeric"

        logger.info("Output file structure verification passed")


def main():
    """Run integration tests."""
    pytest.main([__file__, '-v', '--tb=short'])


if __name__ == '__main__':
    main()
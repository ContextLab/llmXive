"""
Unit tests for SMILES ingestion validation logic.
"""
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from pathlib import Path
import tempfile
import os

from code.data.ingest import (
    validate_smiles,
    count_atoms,
    process_smiles_chunk,
    validate_schema_compatibility,
    write_chunk_to_parquet
)
from code.utils.validators import is_valid_smiles

class TestSMILESValidation:
    """Tests for SMILES validation functions."""

    def test_valid_smiles(self):
        """Test that valid SMILES are accepted."""
        valid_smiles = ["CCO", "c1ccccc1", "CC(=O)O", "C[C@H](O)C(=O)O"]
        for smiles in valid_smiles:
            assert validate_smiles(smiles) is True
            assert is_valid_smiles(smiles) is True

    def test_invalid_smiles(self):
        """Test that invalid SMILES are rejected."""
        invalid_smiles = ["", "invalid", "C((", "123", "CCO("]
        for smiles in invalid_smiles:
            assert validate_smiles(smiles) is False
            assert is_valid_smiles(smiles) is False

    def test_empty_string(self):
        """Test handling of empty strings."""
        assert validate_smiles("") is False

    def test_none_input(self):
        """Test handling of None input."""
        with pytest.raises(Exception):
            validate_smiles(None)

class TestAtomCounting:
    """Tests for atom counting functions."""

    def test_correct_atom_count(self):
        """Test that atom counts are correct."""
        test_cases = [
            ("CCO", 3),  # Ethanol
            ("c1ccccc1", 6),  # Benzene
            ("CC(=O)O", 3),  # Acetic acid
            ("C", 1),  # Methane
        ]
        for smiles, expected in test_cases:
            assert count_atoms(smiles) == expected

    def test_invalid_smiles_atom_count(self):
        """Test atom count for invalid SMILES."""
        assert count_atoms("invalid") == -1
        assert count_atoms("") == -1

class TestChunkProcessing:
    """Tests for chunk processing logic."""

    def test_valid_chunk_processing(self):
        """Test processing of a chunk with all valid molecules."""
        chunk = [
            {"smiles": "CCO", "source": "test"},
            {"smiles": "c1ccccc1", "source": "test"},
        ]
        valid, excluded = process_smiles_chunk(chunk)
        assert len(valid) == 2
        assert len(excluded) == 0

    def test_invalid_smiles_in_chunk(self):
        """Test handling of invalid SMILES in a chunk."""
        chunk = [
            {"smiles": "CCO", "source": "test"},
            {"smiles": "invalid", "source": "test"},
        ]
        valid, excluded = process_smiles_chunk(chunk)
        assert len(valid) == 1
        assert len(excluded) == 0

    def test_max_atoms_filter(self):
        """Test filtering of molecules exceeding max atoms."""
        # Create a molecule with >100 atoms (e.g., long chain)
        long_chain = "C" * 101  # This creates a chain of 101 carbons
        chunk = [
            {"smiles": "CCO", "source": "test"},
            {"smiles": long_chain, "source": "test"},
        ]
        valid, excluded = process_smiles_chunk(chunk)
        assert len(valid) == 1
        assert len(excluded) == 1
        assert excluded[0]["atom_count"] > 100

    def test_empty_chunk(self):
        """Test processing of an empty chunk."""
        chunk = []
        valid, excluded = process_smiles_chunk(chunk)
        assert len(valid) == 0
        assert len(excluded) == 0

class TestSchemaValidation:
    """Tests for schema compatibility validation."""

    def test_valid_schema(self):
        """Test validation of a dataset with required fields."""
        mock_dataset = MagicMock()
        mock_dataset.column_names = ["smiles", "other_field"]
        is_valid, missing = validate_schema_compatibility(mock_dataset)
        assert is_valid is True
        assert len(missing) == 0

    def test_missing_smiles_field(self):
        """Test validation of a dataset missing the SMILES field."""
        mock_dataset = MagicMock()
        mock_dataset.column_names = ["other_field"]
        is_valid, missing = validate_schema_compatibility(mock_dataset)
        assert is_valid is False
        assert "smiles" in missing

class TestParquetWriting:
    """Tests for Parquet file writing."""

    def test_write_chunk_to_parquet(self):
        """Test writing a chunk to Parquet."""
        valid_molecules = [
            {"smiles": "CCO", "atom_count": 3, "source": "test"},
            {"smiles": "c1ccccc1", "atom_count": 6, "source": "test"},
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily change OUTPUT_DIR
            import code.data.ingest as ingest_module
            original_output_dir = ingest_module.OUTPUT_DIR
            ingest_module.OUTPUT_DIR = Path(tmpdir)
            
            try:
                output_path = write_chunk_to_parquet(valid_molecules, 0)
                assert output_path is not None
                assert os.path.exists(output_path)
                
                # Verify content
                df = pd.read_parquet(output_path)
                assert len(df) == 2
                assert "smiles" in df.columns
                assert "atom_count" in df.columns
            finally:
                ingest_module.OUTPUT_DIR = original_output_dir

    def test_empty_chunk_write(self):
        """Test writing an empty chunk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import code.data.ingest as ingest_module
            original_output_dir = ingest_module.OUTPUT_DIR
            ingest_module.OUTPUT_DIR = Path(tmpdir)
            
            try:
                output_path = write_chunk_to_parquet([], 0)
                assert output_path == ""  # Should return empty string for empty chunk
            finally:
                ingest_module.OUTPUT_DIR = original_output_dir
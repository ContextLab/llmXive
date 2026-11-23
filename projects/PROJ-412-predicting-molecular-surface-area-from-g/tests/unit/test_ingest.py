"""
Unit tests for the SMILES ingestion module.
"""
import pytest
import sys
from pathlib import Path
import tempfile
import gzip
import json

# Add project root to path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from rdkit import Chem
from code.data.ingest import validate_smiles, process_smiles_file

class TestValidateSmiles:
    def test_valid_smiles(self):
        """Test with a known valid SMILES string."""
        smiles = "CCO" # Ethanol
        is_valid, error = validate_smiles(smiles)
        assert is_valid is True
        assert error is None

    def test_invalid_smiles_syntax(self):
        """Test with a known invalid SMILES string."""
        smiles = "CC(" # Incomplete
        is_valid, error = validate_smiles(smiles)
        assert is_valid is False
        assert "failed to parse" in error.lower() or "None" in error

    def test_empty_string(self):
        """Test with an empty string."""
        is_valid, error = validate_smiles("")
        assert is_valid is False
        assert "Empty" in error

    def test_none_input(self):
        """Test with None input."""
        is_valid, error = validate_smiles(None)
        assert is_valid is False

class TestProcessSmilesFile:
    def test_process_valid_file(self):
        """Test processing a valid SMILES file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "test.smi.gz"
            output_path = Path(tmpdir) / "test.csv"
            
            # Create a fake gzipped SMILES file
            content = "CCO\tethanol\nCC\tethane\nC\tmethane\n"
            with gzip.open(input_path, 'wt', encoding='utf-8') as f:
                f.write(content)
            
            stats = process_smiles_file(input_path, output_path)
            
            assert stats['total_rows'] == 3
            assert stats['valid_rows'] == 3
            assert stats['invalid_rows'] == 0
            assert output_path.exists()

    def test_process_file_with_invalid(self):
        """Test processing a file containing invalid SMILES."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "test.smi.gz"
            output_path = Path(tmpdir) / "test.csv"
            
            # Mix of valid and invalid
            content = "CCO\tethanol\nCC(\tinvalid\nC\tmethane\n"
            with gzip.open(input_path, 'wt', encoding='utf-8') as f:
                f.write(content)
            
            stats = process_smiles_file(input_path, output_path)
            
            assert stats['total_rows'] == 3
            assert stats['valid_rows'] == 2
            assert stats['invalid_rows'] == 1
            
            # Check validation log exists
            log_path = output_path.parent / "ingestion_validation.json"
            assert log_path.exists()
            
            with open(log_path) as f:
                log_data = json.load(f)
            assert len(log_data['sample_errors']) > 0
            assert log_data['sample_errors'][0]['error'] is not None

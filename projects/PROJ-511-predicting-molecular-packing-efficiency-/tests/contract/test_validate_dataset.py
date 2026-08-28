import os
import sys
import pytest
import pandas as pd
import yaml
import tempfile
import shutil
from pathlib import Path

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from validate_dataset import load_schema, validate_schema, cross_reference_cif_ids
from config import get_data_dir, get_base_dir

class TestValidateDataset:
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        temp_base = tempfile.mkdtemp()
        temp_data = os.path.join(temp_base, "data")
        temp_raw_cif = os.path.join(temp_data, "raw_cif")
        temp_contracts = os.path.join(temp_base, "contracts")
        
        os.makedirs(temp_raw_cif)
        os.makedirs(temp_contracts)
        
        yield {
            "base": temp_base,
            "data": temp_data,
            "raw_cif": temp_raw_cif,
            "contracts": temp_contracts
        }
        
        shutil.rmtree(temp_base)

    @pytest.fixture
    def mock_schema(self, temp_dirs):
        """Create a minimal valid schema file."""
        schema_path = os.path.join(temp_dirs["contracts"], "test_schema.yaml")
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["cod_id", "smiles"],
            "properties": {
                "cod_id": {"type": "string", "pattern": "^COD-\\d+$"},
                "smiles": {"type": "string", "minLength": 1}
            }
        }
        with open(schema_path, 'w') as f:
            yaml.dump(schema, f)
        return schema_path

    @pytest.fixture
    def mock_csv(self, temp_dirs):
        """Create a valid CSV file."""
        csv_path = os.path.join(temp_dirs["data"], "test_dataset.csv")
        df = pd.DataFrame({
            "cod_id": ["COD-12345", "COD-67890"],
            "smiles": ["CCO", "CC(=O)O"]
        })
        df.to_csv(csv_path, index=False)
        return csv_path

    @pytest.fixture
    def mock_cif_files(self, temp_dirs):
        """Create dummy CIF files."""
        for cod_id in ["COD-12345", "COD-67890"]:
            cif_path = os.path.join(temp_dirs["raw_cif"], f"{cod_id}.cif")
            with open(cif_path, 'w') as f:
                f.write(f"# Dummy CIF for {cod_id}\n")
        return temp_dirs["raw_cif"]

    def test_load_schema(self, mock_schema):
        """Test loading a YAML schema."""
        schema = load_schema(mock_schema)
        assert "type" in schema
        assert schema["type"] == "object"

    def test_validate_schema_valid(self, mock_csv, mock_schema):
        """Test validation with valid data."""
        df = pd.read_csv(mock_csv)
        schema = load_schema(mock_schema)
        errors = validate_schema(df, schema)
        assert len(errors) == 0

    def test_validate_schema_invalid(self, temp_dirs, mock_schema):
        """Test validation with invalid data (missing required field)."""
        csv_path = os.path.join(temp_dirs["data"], "invalid.csv")
        df = pd.DataFrame({
            "cod_id": ["COD-12345"],
            # Missing 'smiles'
        })
        df.to_csv(csv_path, index=False)
        
        df = pd.read_csv(csv_path)
        schema = load_schema(mock_schema)
        errors = validate_schema(df, schema)
        assert len(errors) > 0
        assert any("smiles" in err for err in errors)

    def test_cross_reference_cif_ids_all_present(self, mock_csv, mock_cif_files):
        """Test cross-referencing when all CIFs are present."""
        missing = cross_reference_cif_ids(mock_csv, mock_cif_files)
        assert len(missing) == 0

    def test_cross_reference_cif_ids_missing(self, temp_dirs, mock_cif_files):
        """Test cross-referencing when some CIFs are missing."""
        # Create CSV with a new ID not in CIF dir
        csv_path = os.path.join(temp_dirs["data"], "missing.csv")
        df = pd.DataFrame({
            "cod_id": ["COD-12345", "COD-99999"],
            "smiles": ["CCO", "CCO"]
        })
        df.to_csv(csv_path, index=False)
        
        missing = cross_reference_cif_ids(csv_path, mock_cif_files)
        assert len(missing) == 1
        assert "COD-99999" in missing

    def test_cross_reference_cif_ids_dir_missing(self, mock_csv, temp_dirs):
        """Test cross-referencing when CIF directory does not exist."""
        non_existent_dir = os.path.join(temp_dirs["data"], "non_existent")
        missing = cross_reference_cif_ids(mock_csv, non_existent_dir)
        # Should return empty list or handle gracefully
        assert missing == []
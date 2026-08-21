"""
Unit tests for write_metadata.py (Task T013b).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd

# Import the module under test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from write_metadata import (
    load_raw_data,
    validate_metadata_structure,
    process_metadata_entries,
    main
)
from data_ingestion_metadata import parse_uncertainty, extract_instrument_model

class TestLoadRawData:
    def test_load_raw_data_success(self, tmp_path):
        """Test loading a valid CSV file."""
        csv_path = tmp_path / "test.csv"
        df_content = """formula,T_d,metadata_text
        CsPbI3,350,TA Instruments Q500, ±5°C
        MAPbBr3,400,Mettler Toledo TGA/DSC, precision ±10°C
        """
        csv_path.write_text(df_content)
        
        with patch("write_metadata.RAW_DATA_PATH", csv_path):
            df = load_raw_data()
            assert len(df) == 2
            assert "formula" in df.columns
            assert "T_d" in df.columns
            assert "metadata_text" in df.columns

    def test_load_raw_data_missing_file(self, tmp_path):
        """Test loading when file does not exist."""
        with patch("write_metadata.RAW_DATA_PATH", tmp_path / "nonexistent.csv"):
            with pytest.raises(FileNotFoundError):
                load_raw_data()

    def test_load_raw_data_missing_columns(self, tmp_path):
        """Test loading when required columns are missing."""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("formula,T_d\nCsPbI3,350\n")
        
        with patch("write_metadata.RAW_DATA_PATH", csv_path):
            with pytest.raises(ValueError, match="Missing required columns"):
                load_raw_data()

class TestValidateMetadataStructure:
    def test_valid_structure(self):
        """Test validation with valid metadata structure."""
        entries = [
            {
                "index": 0,
                "formula": "CsPbI3",
                "instrument_model": "TA Instruments Q500",
                "uncertainty": {
                    "unit": "Celsius",
                    "type": "single",
                    "value": 5.0
                },
                "raw_metadata_text": "TA Instruments Q500, ±5°C"
            }
        ]
        assert validate_metadata_structure(entries) is True

    def test_invalid_entry_type(self):
        """Test validation when an entry is not a dict."""
        entries = ["not a dict"]
        assert validate_metadata_structure(entries) is False

    def test_missing_field(self):
        """Test validation when a required field is missing."""
        entries = [
            {
                "index": 0,
                "formula": "CsPbI3",
                # Missing instrument_model, uncertainty, raw_metadata_text
            }
        ]
        assert validate_metadata_structure(entries) is False

    def test_invalid_uncertainty_type(self):
        """Test validation when uncertainty type is invalid."""
        entries = [
            {
                "index": 0,
                "formula": "CsPbI3",
                "instrument_model": "TA Instruments Q500",
                "uncertainty": {
                    "unit": "Celsius",
                    "type": "invalid_type",
                    "value": 5.0
                },
                "raw_metadata_text": "TA Instruments Q500, ±5°C"
            }
        ]
        assert validate_metadata_structure(entries) is False

    def test_invalid_uncertainty_unit(self):
        """Test validation when uncertainty unit is invalid."""
        entries = [
            {
                "index": 0,
                "formula": "CsPbI3",
                "instrument_model": "TA Instruments Q500",
                "uncertainty": {
                    "unit": "Kelvin",
                    "type": "single",
                    "value": 5.0
                },
                "raw_metadata_text": "TA Instruments Q500, ±5°C"
            }
        ]
        assert validate_metadata_structure(entries) is False

class TestProcessMetadataEntries:
    def test_process_entries(self):
        """Test processing dataframe entries into metadata structure."""
        df = pd.DataFrame({
            "formula": ["CsPbI3", "MAPbBr3"],
            "T_d": [350, 400],
            "metadata_text": [
                "TA Instruments Q500, ±5°C",
                "Mettler Toledo TGA/DSC, precision ±10°C"
            ]
        })
        
        entries = process_metadata_entries(df)
        
        assert len(entries) == 2
        
        # Check first entry
        assert entries[0]["formula"] == "CsPbI3"
        assert entries[0]["index"] == 0
        assert entries[0]["instrument_model"] == "TA Instruments Q500"
        assert entries[0]["uncertainty"]["type"] == "single"
        assert entries[0]["uncertainty"]["value"] == 5.0
        
        # Check second entry
        assert entries[1]["formula"] == "MAPbBr3"
        assert entries[1]["index"] == 1
        assert entries[1]["instrument_model"] == "Mettler Toledo TGA/DSC"
        assert entries[1]["uncertainty"]["type"] == "single"
        assert entries[1]["uncertainty"]["value"] == 10.0

class TestMain:
    @patch("write_metadata.load_raw_data")
    @patch("write_metadata.process_metadata_entries")
    @patch("write_metadata.validate_metadata_structure")
    @patch("write_metadata.METADATA_OUTPUT_PATH")
    def test_main_success(self, mock_path, mock_validate, mock_process, mock_load, tmp_path):
        """Test successful execution of main function."""
        mock_load.return_value = pd.DataFrame({
            "formula": ["CsPbI3"],
            "T_d": [350],
            "metadata_text": ["TA Instruments Q500, ±5°C"]
        })
        mock_process.return_value = [
            {
                "index": 0,
                "formula": "CsPbI3",
                "instrument_model": "TA Instruments Q500",
                "uncertainty": {"unit": "Celsius", "type": "single", "value": 5.0},
                "raw_metadata_text": "TA Instruments Q500, ±5°C"
            }
        ]
        mock_validate.return_value = True
        
        # Create a temporary file for output
        output_file = tmp_path / "metadata.json"
        mock_path.__truediv__.return_value = output_file
        mock_path.__fspath__.return_value = str(output_file)
        
        # Patch the Path.exists and stat methods
        with patch.object(type(output_file), 'exists', return_value=True):
            with patch.object(type(output_file), 'stat') as mock_stat:
                mock_stat.return_value = MagicMock(st_size=100)
                main()
        
        # Verify output file was created
        assert output_file.exists()
        
        # Verify content
        with open(output_file) as f:
            data = json.load(f)
            assert "processed_at" in data
            assert "source_file" in data
            assert "entries" in data
            assert len(data["entries"]) == 1
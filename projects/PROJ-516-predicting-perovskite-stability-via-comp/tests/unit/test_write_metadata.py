import json
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

# Import the module under test
# Note: We need to ensure the path is set up correctly for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from write_metadata import process_metadata_entries, validate_metadata_structure, main

class TestProcessMetadataEntries:
    def test_process_valid_records(self):
        """Test processing records with valid instrument metadata."""
        records = [
            {"formula": "CsPbI3", "instrument_model": "TA Instruments", "manufacturer": "TA Instruments", "source": "NREL"},
            {"formula": "FAPbI3", "instrument_model": "Mettler Toledo", "manufacturer": "Mettler Toledo", "source": "MP"}
        ]
        result = process_metadata_entries(records)
        
        assert len(result) == 2
        assert result[0]["formula"] == "CsPbI3"
        assert result[0]["instrument_model"] == "TA Instruments"
        assert result[0]["manufacturer"] == "TA Instruments"
        assert result[0]["precision_source"] == "source"
        
        assert result[1]["formula"] == "FAPbI3"
        assert result[1]["instrument_model"] == "Mettler Toledo"
        assert result[1]["manufacturer"] == "Mettler Toledo"
        assert result[1]["precision_source"] == "source"

    def test_process_missing_instrumentation(self):
        """Test processing records with missing instrument metadata."""
        records = [
            {"formula": "CsPbI3", "source": "NREL"},
            {"formula": "FAPbI3", "source": "MP"}
        ]
        result = process_metadata_entries(records)
        
        assert len(result) == 2
        # Should default to Unknown
        assert result[0]["instrument_model"] == "Unknown"
        assert result[0]["manufacturer"] == "Unknown"
        assert result[0]["precision_source"] == "default"

    def test_process_partial_instrumentation(self):
        """Test processing records with partial instrument metadata."""
        records = [
            {"formula": "CsPbI3", "instrument_model": "TA Instruments", "source": "NREL"},
            {"formula": "FAPbI3", "manufacturer": "Mettler Toledo", "source": "MP"}
        ]
        result = process_metadata_entries(records)
        
        # Should default to Unknown if either is missing
        assert result[0]["instrument_model"] == "Unknown"
        assert result[0]["manufacturer"] == "Unknown"
        assert result[0]["precision_source"] == "default"

class TestValidateMetadataStructure:
    def test_valid_metadata(self):
        """Test validation of correctly structured metadata."""
        metadata = [
            {"formula": "CsPbI3", "instrument_model": "TA Instruments", "manufacturer": "TA Instruments", "precision_source": "source"},
            {"formula": "FAPbI3", "instrument_model": "Unknown", "manufacturer": "Unknown", "precision_source": "default"}
        ]
        assert validate_metadata_structure(metadata) is True

    def test_missing_keys(self):
        """Test validation fails on missing keys."""
        metadata = [
            {"formula": "CsPbI3", "instrument_model": "TA Instruments"}
        ]
        assert validate_metadata_structure(metadata) is False

    def test_invalid_precision_source(self):
        """Test validation fails on invalid precision_source value."""
        metadata = [
            {"formula": "CsPbI3", "instrument_model": "TA Instruments", "manufacturer": "TA Instruments", "precision_source": "invalid"}
        ]
        assert validate_metadata_structure(metadata) is False

    def test_non_dict_entry(self):
        """Test validation fails on non-dictionary entry."""
        metadata = [
            "not a dict"
        ]
        assert validate_metadata_structure(metadata) is False

class TestMain:
    def test_main_success(self, tmp_path):
        """Test main function executes successfully."""
        # Create a temporary CSV file
        csv_path = tmp_path / "perovskites_merged.csv"
        df = pd.DataFrame([
            {"formula": "CsPbI3", "instrument_model": "TA Instruments", "manufacturer": "TA Instruments", "source": "NREL"},
            {"formula": "FAPbI3", "source": "MP"}
        ])
        df.to_csv(csv_path, index=False)

        # Mock the paths
        with patch('write_metadata.RAW_DATA_PATH', csv_path), \
             patch('write_metadata.METADATA_OUTPUT_PATH', tmp_path / "metadata.json"), \
             patch('write_metadata.FALLBACK_LOG_PATH', tmp_path / "instrumentation_fallbacks.log"):
            main()

            # Check output file exists
            output_path = tmp_path / "metadata.json"
            assert output_path.exists()
            
            # Check content
            with open(output_path) as f:
                data = json.load(f)
            assert len(data) == 2

    def test_main_missing_input(self, tmp_path):
        """Test main function fails when input file is missing."""
        with patch('write_metadata.RAW_DATA_PATH', tmp_path / "nonexistent.csv"):
            with pytest.raises(SystemExit):
                main()
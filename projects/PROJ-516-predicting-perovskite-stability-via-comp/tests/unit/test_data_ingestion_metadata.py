import pytest
import json
import tempfile
from pathlib import Path
import pandas as pd
from data_ingestion_metadata import parse_uncertainty, extract_instrument_model, process_metadata_entries

class TestParseUncertainty:
    def test_single_value(self):
        result = parse_uncertainty("±5°C")
        assert result is not None
        assert result['value'] == 5.0
        assert result['unit'] == 'Celsius'
        assert result['type'] == 'single'

    def test_range_value(self):
        result = parse_uncertainty("±5-10°C")
        assert result is not None
        assert result['value'] == [5.0, 10.0]
        assert result['unit'] == 'Celsius'
        assert result['type'] == 'range'

    def test_with_spaces(self):
        result = parse_uncertainty("± 5 °C")
        assert result is not None
        assert result['value'] == 5.0

    def test_invalid_input(self):
        assert parse_uncertainty(None) is None
        assert parse_uncertainty("") is None
        assert parse_uncertainty("invalid") is None

class TestExtractInstrumentModel:
    def test_ta_instruments(self):
        text = "Measurement performed on TA Instruments Q500 TGA"
        result = extract_instrument_model(text)
        assert result is not None
        assert "TA Instruments" in result

    def test_mettler_toledo(self):
        text = "Data collected using Mettler Toledo TGA/DSC 1"
        result = extract_instrument_model(text)
        assert result is not None
        assert "Mettler Toledo" in result

    def test_perkinelmer(self):
        text = "Thermal analysis conducted on PerkinElmer TGA 4000"
        result = extract_instrument_model(text)
        assert result is not None
        assert "PerkinElmer" in result

    def test_no_instrument_found(self):
        text = "No instrument information provided"
        result = extract_instrument_model(text)
        assert result is None

class TestProcessMetadataEntries:
    def test_process_metadata_creates_file(self):
        # Create a temporary CSV with sample data
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "test_data.csv"
            json_path = Path(tmpdir) / "test_metadata.json"
            
            # Create sample data
            data = {
                'formula': ['CsPbI3', 'MAPbBr3', 'FAPbI3'],
                'T_d': [450, 420, 430],
                'notes': [
                    'Measured on TA Instruments Q500, ±5°C',
                    'Mettler Toledo TGA/DSC, precision ±10°C',
                    'No instrument info'
                ]
            }
            df = pd.DataFrame(data)
            df.to_csv(csv_path, index=False)
            
            # Run processing
            process_metadata_entries(str(csv_path), str(json_path))
            
            # Verify output file exists
            assert json_path.exists()
            
            # Verify content
            with open(json_path, 'r') as f:
                metadata = json.load(f)
            
            assert 'entries' in metadata
            assert len(metadata['entries']) == 2  # Only 2 entries have metadata
            
            # Check first entry
            first_entry = metadata['entries'][0]
            assert first_entry['formula'] == 'CsPbI3'
            assert first_entry['instrument_model'] is not None
            assert first_entry['uncertainty'] is not None

    def test_process_metadata_empty_input(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "empty_data.csv"
            json_path = Path(tmpdir) / "empty_metadata.json"
            
            # Create empty CSV with just headers
            data = {'formula': [], 'T_d': [], 'notes': []}
            df = pd.DataFrame(data)
            df.to_csv(csv_path, index=False)
            
            # Run processing
            process_metadata_entries(str(csv_path), str(json_path))
            
            # Verify output file exists
            assert json_path.exists()
            
            with open(json_path, 'r') as f:
                metadata = json.load(f)
            
            assert len(metadata['entries']) == 0

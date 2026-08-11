import pytest
import pandas as pd
from code.data_ingestion_metadata import parse_uncertainty, extract_instrument_model, process_metadata_entries

class TestParseUncertainty:
    def test_parse_celsius_with_symbol(self):
        result = parse_uncertainty("±5°C")
        assert result is not None
        assert result['value'] == 5.0
        assert result['unit'] == 'C'

    def test_parse_celsius_with_space(self):
        result = parse_uncertainty("± 10 °C")
        assert result is not None
        assert result['value'] == 10.0
        assert result['unit'] == 'C'

    def test_parse_uncertainty_label(self):
        result = parse_uncertainty("uncertainty: 7 degrees")
        assert result is not None
        assert result['value'] == 7.0

    def test_parse_precision_label(self):
        result = parse_uncertainty("precision 8.5 C")
        assert result is not None
        assert result['value'] == 8.5

    def test_none_input(self):
        assert parse_uncertainty(None) is None
        assert parse_uncertainty("") is None

    def test_invalid_string(self):
        result = parse_uncertainty("no uncertainty mentioned")
        assert result is None

class TestExtractInstrumentModel:
    def test_q_series(self):
        result = extract_instrument_model("TGA Q500")
        assert result == "TGA Q500"

    def test_sdt_series(self):
        result = extract_instrument_model("SDT Q600")
        assert result == "SDT Q600"

    def test_mettler_toledo(self):
        result = extract_instrument_model("Mettler Toledo TGA/DSC 1")
        assert "Mettler Toledo" in result

    def test_no_match(self):
        result = extract_instrument_model("no instrument mentioned")
        assert result is None

    def test_none_input(self):
        assert extract_instrument_model(None) is None

class TestProcessMetadataEntries:
    def test_process_dataframe(self):
        data = {
            'id': [1, 2, 3],
            'source_metadata': [
                "TGA Q500, ±5°C",
                "SDT Q600, uncertainty 10",
                "No instrument data"
            ]
        }
        df = pd.DataFrame(data)
        
        result = process_metadata_entries(df)
        
        assert len(result) == 3
        assert result[0]['instrument_model'] == "TGA Q500"
        assert result[0]['uncertainty']['value'] == 5.0
        assert result[1]['uncertainty']['value'] == 10.0
        assert result[2]['instrument_model'] is None

    def test_missing_column(self):
        df = pd.DataFrame({'id': [1]})
        result = process_metadata_entries(df, metadata_column='nonexistent')
        assert len(result) == 0

import json
import pytest
from pathlib import Path
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from data_ingestion_metadata import (
    parse_uncertainty,
    extract_instrument_model,
    process_metadata_entries
)


class TestParseUncertainty:
    def test_parse_explicit_value(self):
        result = parse_uncertainty("±5°C")
        assert result["value"] == 5.0
        assert result["unit"] == "°C"
        assert result["source"] == "parsed"

    def test_parse_numeric_only(self):
        result = parse_uncertainty("10")
        assert result["value"] == 10.0
        assert result["unit"] == "°C"

    def test_parse_none_returns_default(self):
        result = parse_uncertainty(None)
        assert result["value"] == 10.0
        assert result["source"] == "default"

    def test_parse_empty_string_returns_default(self):
        result = parse_uncertainty("")
        assert result["value"] == 10.0
        assert result["source"] == "default"

    def test_parse_invalid_returns_default(self):
        result = parse_uncertainty("invalid")
        assert result["value"] == 10.0
        assert result["source"] == "default"


class TestExtractInstrumentModel:
    def test_extract_tga_model(self):
        result = extract_instrument_model("TGA Q500, heating rate 10°C/min")
        assert "TGA" in result or "Q500" in result

    def test_extract_sta_model(self):
        result = extract_instrument_model("STA 449 F1 Jupiter")
        assert "STA" in result or "449" in result

    def test_none_returns_unknown(self):
        result = extract_instrument_model(None)
        assert result == "unknown"

    def test_empty_returns_unknown(self):
        result = extract_instrument_model("")
        assert result == "unknown"


class TestProcessMetadataEntries:
    @pytest.fixture
    def sample_df(self):
        data = {
            "entry_id": ["entry_1", "entry_2"],
            "formula": ["CsPbI3", "MAPbBr3"],
            "T_d": [350.0, 400.0],
            "instrument_metadata": [
                "TGA Q500, ±5°C uncertainty",
                "STA 449, ±10°C uncertainty"
            ],
            "uncertainty": ["±5°C", "±10°C"],
            "source_citation": ["DOI:10.1038/s41560-020-00700-0", "DOI:10.1021/jacs.9b12345"],
            "validated": [True, True]
        }
        return pd.DataFrame(data)

    def test_process_returns_list_of_dicts(self, sample_df):
        result = process_metadata_entries(sample_df)
        assert isinstance(result, list)
        assert len(result) == 2
        assert isinstance(result[0], dict)

    def test_entry_contains_required_fields(self, sample_df):
        result = process_metadata_entries(sample_df)
        entry = result[0]
        required_fields = [
            "entry_id", "formula", "T_d", "instrument_model",
            "uncertainty", "source_citation", "validated"
        ]
        for field in required_fields:
            assert field in entry

    def test_uncertainty_structure(self, sample_df):
        result = process_metadata_entries(sample_df)
        uncertainty = result[0]["uncertainty"]
        assert "value" in uncertainty
        assert "unit" in uncertainty
        assert "source" in uncertainty
        assert isinstance(uncertainty["value"], float)
        assert uncertainty["unit"] == "°C"

    def test_handles_empty_dataframe(self):
        empty_df = pd.DataFrame(columns=["entry_id", "formula", "T_d"])
        result = process_metadata_entries(empty_df)
        assert result == []

    def test_schema_adherence(self, sample_df, tmp_path):
        """Verify output matches expected schema structure."""
        result = process_metadata_entries(sample_df)

        # Verify structure matches contracts/metadata.schema.yaml expectations
        for entry in result:
            assert isinstance(entry["entry_id"], str)
            assert isinstance(entry["formula"], str)
            assert isinstance(entry["T_d"], float)
            assert isinstance(entry["instrument_model"], str)
            assert isinstance(entry["uncertainty"], dict)
            assert "value" in entry["uncertainty"]
            assert "unit" in entry["uncertainty"]
            assert isinstance(entry["source_citation"], str)
            assert isinstance(entry["validated"], bool)

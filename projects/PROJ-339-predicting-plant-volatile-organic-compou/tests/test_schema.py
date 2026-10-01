"""
Tests for T007a: Schema validation implementation.
Verifies that the schema definitions are correct and can validate data.
"""
import pytest
import os
import sys
import tempfile
from pathlib import Path
import json

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from utils.schema_validator import (
    Sample, GenomicFeature, EnvironmentalFeature, VOCProfile,
    validate_record, validate_csv_dummy, generate_dummy_csv, load_schema
)

SCHEMA_PATH = "specs/001-predict-voc-profiles/contracts/dataset.schema.yaml"

class TestSchemaDefinitions:
    def test_sample_valid(self):
        data = {
            "sample_id": "S001",
            "species": "Arabidopsis thaliana",
            "tissue_type": "leaf",
            "collection_date": "2023-01-15"
        }
        assert validate_record(data, "Sample") is True

    def test_sample_invalid_date(self):
        data = {
            "sample_id": "S001",
            "species": "Arabidopsis thaliana",
            "tissue_type": "leaf",
            "collection_date": "2023-13-45" # Invalid date
        }
        with pytest.raises(ValueError):
            validate_record(data, "Sample")

    def test_sample_missing_required(self):
        data = {
            "sample_id": "S001",
            "species": "Arabidopsis thaliana"
            # Missing tissue_type and collection_date
        }
        with pytest.raises(Exception):
            validate_record(data, "Sample")

    def test_genomic_feature_valid(self):
        data = {
            "sample_id": "S001",
            "gene_id": "AT1G01010",
            "tpm": 15.5,
            "raw_count": 120
        }
        assert validate_record(data, "GenomicFeature") is True

    def test_environmental_feature_valid(self):
        data = {
            "sample_id": "S001",
            "temperature": 25.0,
            "light_intensity": 300.0,
            "co2_level": 400.0
        }
        assert validate_record(data, "EnvironmentalFeature") is True

    def test_voc_profile_valid(self):
        data = {
            "sample_id": "S001",
            "compound_name": "Limonene",
            "emission_rate": 150.5,
            "unit": "ng g-1 h-1"
        }
        assert validate_record(data, "VOCProfile") is True

class TestSchemaFile:
    def test_schema_file_exists(self):
        assert os.path.exists(SCHEMA_PATH), f"Schema file not found at {SCHEMA_PATH}"

    def test_schema_loads(self):
        schema = load_schema(SCHEMA_PATH)
        assert "definitions" in schema
        assert "Sample" in schema["definitions"]
        assert "GenomicFeature" in schema["definitions"]
        assert "EnvironmentalFeature" in schema["definitions"]
        assert "VOCProfile" in schema["definitions"]

class TestDummyCSVGeneration:
    def test_generate_and_validate_sample(self):
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            generate_dummy_csv(tmp_path, "Sample")
            assert os.path.exists(tmp_path)
            assert validate_csv_dummy(tmp_path, SCHEMA_PATH) is True
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_generate_and_validate_genomic(self):
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            generate_dummy_csv(tmp_path, "GenomicFeature")
            assert os.path.exists(tmp_path)
            assert validate_csv_dummy(tmp_path, SCHEMA_PATH) is True
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_generate_and_validate_environmental(self):
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            generate_dummy_csv(tmp_path, "EnvironmentalFeature")
            assert os.path.exists(tmp_path)
            assert validate_csv_dummy(tmp_path, SCHEMA_PATH) is True
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_generate_and_validate_voc(self):
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            generate_dummy_csv(tmp_path, "VOCProfile")
            assert os.path.exists(tmp_path)
            assert validate_csv_dummy(tmp_path, SCHEMA_PATH) is True
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
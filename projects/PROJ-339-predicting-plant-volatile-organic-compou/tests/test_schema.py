"""
Tests for T007a: Dataset Schema Validation.
Verifies that the schema definition is valid and can validate dummy data.
"""
import pytest
import json
import os
import sys
from pathlib import Path
from datetime import date

# Add code directory to path
code_dir = Path(__file__).parent.parent / 'code'
sys.path.insert(0, str(code_dir))

from utils.schema_validator import (
    Sample, 
    GenomicFeature, 
    EnvironmentalFeature, 
    VOCProfile,
    validate_record,
    generate_dummy_csv,
    validate_csv_dummy
)

class TestPydanticModels:
    def test_valid_sample(self):
        data = {
            'sample_id': 'S001',
            'species': 'Arabidopsis thaliana',
            'tissue_type': 'leaf',
            'collection_date': '2023-05-15'
        }
        s = Sample(**data)
        assert s.sample_id == 'S001'
        assert s.species == 'Arabidopsis thaliana'

    def test_invalid_sample_missing_required(self):
        data = {
            'sample_id': 'S001',
            # missing species
            'tissue_type': 'leaf',
            'collection_date': '2023-05-15'
        }
        with pytest.raises(Exception): # Pydantic ValidationError
            Sample(**data)

    def test_valid_genomic_feature(self):
        data = {
            'sample_id': 'S001',
            'gene_id': 'AT1G01010',
            'tpm_value': 12.5
        }
        g = GenomicFeature(**data)
        assert g.tpm_value == 12.5

    def test_valid_environmental_feature(self):
        data = {
            'sample_id': 'S001',
            'temperature': 24.5,
            'light_intensity': 400.0,
            'co2_level': 410.0
        }
        e = EnvironmentalFeature(**data)
        assert e.temperature == 24.5

    def test_valid_voc_profile(self):
        data = {
            'sample_id': 'S001',
            'compound_id': '123-45-6',
            'concentration': 5.2
        }
        v = VOCProfile(**data)
        assert v.concentration == 5.2

class TestSchemaValidation:
    def test_validate_record_function(self):
        record = {
            'sample_id': 'S001',
            'species': 'Arabidopsis thaliana',
            'tissue_type': 'leaf',
            'collection_date': '2023-05-15'
        }
        assert validate_record(record, 'Sample') is True

    def test_validate_invalid_record(self):
        record = {
            'sample_id': 'S001',
            # missing species
            'tissue_type': 'leaf',
            'collection_date': '2023-05-15'
        }
        with pytest.raises(Exception):
            validate_record(record, 'Sample')

class TestDummyCSVGeneration:
    def test_generate_and_validate(self, tmp_path):
        dummy_path = tmp_path / 'dummy.csv'
        schema_path = Path(__file__).parent.parent / 'specs' / '001-predict-voc-profiles' / 'contracts' / 'dataset.schema.yaml'
        
        # Ensure schema exists for the test
        assert schema_path.exists(), "Schema file missing for test"

        generate_dummy_csv(str(dummy_path))
        assert dummy_path.exists()

        results = validate_csv_dummy(str(dummy_path), str(schema_path))
        assert results['total_records'] == 4
        assert results['valid_records'] == 4
        assert results['invalid_records'] == 0
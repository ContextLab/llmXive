"""
Unit tests for colony and SNP schema validators.
"""
import pytest
from code.utils.validators.colony_schema import validate_colony_data, validate_colony_batch
from code.utils.validators.snp_schema import validate_snp_data, validate_snp_batch


class TestColonySchema:
    def test_valid_colony(self):
        data = {
            "colony_id": "COL-001",
            "sampling_date": "2023-05-15",
            "geographic_region": "North America",
            "sampling_year": 2023,
            "varroa_load": 5.2,
            "hive_status": "healthy"
        }
        errors = validate_colony_data(data)
        assert len(errors) == 0

    def test_missing_required_field(self):
        data = {
            "colony_id": "COL-002",
            "sampling_date": "2023-05-15",
            "geographic_region": "North America"
            # missing sampling_year
        }
        errors = validate_colony_data(data)
        assert "Missing required field: sampling_year" in errors

    def test_invalid_hive_status(self):
        data = {
            "colony_id": "COL-003",
            "sampling_date": "2023-05-15",
            "geographic_region": "North America",
            "sampling_year": 2023,
            "hive_status": "unknown_status"
        }
        errors = validate_colony_data(data)
        assert any("Invalid hive_status" in err for err in errors)

    def test_invalid_varroa_load(self):
        data = {
            "colony_id": "COL-004",
            "sampling_date": "2023-05-15",
            "geographic_region": "North America",
            "sampling_year": 2023,
            "varroa_load": -5.0
        }
        errors = validate_colony_data(data)
        assert any("varroa_load cannot be negative" in err for err in errors)


class TestSnpSchema:
    def test_valid_snp(self):
        data = {
            "rs_id": "rs123456",
            "chromosome": "1",
            "position": 100000,
            "allele1": "A",
            "allele2": "G",
            "p_value": 0.001,
            "odds_ratio": 2.5
        }
        errors = validate_snp_data(data)
        assert len(errors) == 0

    def test_missing_required_field(self):
        data = {
            "rs_id": "rs123456",
            "chromosome": "1",
            "position": 100000,
            "allele1": "A"
            # missing allele2
        }
        errors = validate_snp_data(data)
        assert "Missing required field: allele2" in errors

    def test_invalid_allele(self):
        data = {
            "rs_id": "rs123456",
            "chromosome": "1",
            "position": 100000,
            "allele1": "X",
            "allele2": "G"
        }
        errors = validate_snp_data(data)
        assert any("Invalid allele1" in err for err in errors)

    def test_invalid_p_value(self):
        data = {
            "rs_id": "rs123456",
            "chromosome": "1",
            "position": 100000,
            "allele1": "A",
            "allele2": "G",
            "p_value": 1.5
        }
        errors = validate_snp_data(data)
        assert any("p_value must be between 0.0 and 1.0" in err for err in errors)

    def test_invalid_position(self):
        data = {
            "rs_id": "rs123456",
            "chromosome": "1",
            "position": -100,
            "allele1": "A",
            "allele2": "G"
        }
        errors = validate_snp_data(data)
        assert any("position must be positive" in err for err in errors)

class TestBatchValidation:
    def test_colony_batch_validation(self):
        batch = [
            {
                "colony_id": "COL-001",
                "sampling_date": "2023-05-15",
                "geographic_region": "North America",
                "sampling_year": 2023
            },
            {
                "colony_id": "COL-002",
                "sampling_date": "2023-05-15",
                "geographic_region": "North America",
                "sampling_year": 2023,
                "hive_status": "invalid"
            }
        ]
        result = validate_colony_batch(batch)
        assert result["valid_count"] == 1
        assert result["invalid_count"] == 1
        assert len(result["errors"]) > 0

    def test_snp_batch_validation(self):
        batch = [
            {
                "rs_id": "rs123456",
                "chromosome": "1",
                "position": 100000,
                "allele1": "A",
                "allele2": "G"
            },
            {
                "rs_id": "rs789012",
                "chromosome": "1",
                "position": 200000,
                "allele1": "X",
                "allele2": "G"
            }
        ]
        result = validate_snp_batch(batch)
        assert result["valid_count"] == 1
        assert result["invalid_count"] == 1
        assert len(result["errors"]) > 0
"""
Unit tests for the Export Schema Validator (T057)

Tests validation of audit_report.json against the audit_record schema.
"""
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List

import pytest

from code.src.audit.export_schema_validator import (
    load_audit_records_from_json,
    validate_audit_report_schema,
    run_schema_validation,
)
from code.src.utils.logger import get_default_logger


@pytest.fixture
def valid_audit_record() -> Dict[str, Any]:
    """Create a valid audit record matching the schema."""
    return {
        "url": "https://example.com/test",
        "domain": "example.com",
        "extraction_timestamp": "2023-01-01T00:00:00Z",
        "baseline_n": 1000,
        "baseline_successes": 100,
        "treatment_n": 1000,
        "treatment_successes": 120,
        "reported_p_value": 0.03,
        "reported_effect_size": 0.02,
        "reconstructed_p_value": 0.028,
        "reconstructed_effect_size": 0.02,
        "p_value_difference": 0.002,
        "effect_size_difference": 0.0,
        "is_inconsistent": False,
        "sample_size_mismatch": False,
        "data_quality_warning": None,
        "inconsistency_reason": None,
    }


@pytest.fixture
def invalid_audit_record() -> Dict[str, Any]:
    """Create an invalid audit record missing required fields."""
    return {
        "url": "https://example.com/test",
        # Missing required fields: domain, extraction_timestamp, etc.
        "baseline_n": "not_a_number",  # Wrong type
    }


@pytest.fixture
def audit_report_with_valid_records(
    valid_audit_record: Dict[str, Any],
) -> Path:
    """Create a temporary audit report file with valid records."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump([valid_audit_record], f)
        return Path(f.name)


@pytest.fixture
def audit_report_with_invalid_records(
    invalid_audit_record: Dict[str, Any],
) -> Path:
    """Create a temporary audit report file with invalid records."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump([invalid_audit_record], f)
        return Path(f.name)


@pytest.fixture
def schema_path() -> Path:
    """Return the path to the audit_record schema."""
    return Path("code/contracts/audit_record.schema.yaml")


class TestLoadAuditRecordsFromJson:
    def test_load_valid_json_file(
        self,
        audit_report_with_valid_records: Path,
    ):
        """Test loading a valid JSON file."""
        records = load_audit_records_from_json(audit_report_with_valid_records)
        assert len(records) == 1
        assert records[0]["url"] == "https://example.com/test"

    def test_load_nonexistent_file(self):
        """Test loading a nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_audit_records_from_json(Path("nonexistent.json"))

    def test_load_invalid_json_file(self):
        """Test loading an invalid JSON file raises JSONDecodeError."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write("not valid json")
            temp_path = Path(f.name)

        with pytest.raises(json.JSONDecodeError):
            load_audit_records_from_json(temp_path)

        temp_path.unlink()

    def test_load_dict_with_records_key(self):
        """Test loading a JSON file with a 'records' key."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(
                {"records": [{"url": "test"}]},
                f,
            )
            temp_path = Path(f.name)

        records = load_audit_records_from_json(temp_path)
        assert len(records) == 1
        assert records[0]["url"] == "test"

        temp_path.unlink()


class TestValidateAuditReportSchema:
    def test_validate_valid_records(
        self,
        audit_report_with_valid_records: Path,
        schema_path: Path,
    ):
        """Test validating records that conform to the schema."""
        records = load_audit_records_from_json(audit_report_with_valid_records)
        is_valid, errors = validate_audit_report_schema(records, schema_path)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_invalid_records(
        self,
        audit_report_with_invalid_records: Path,
        schema_path: Path,
    ):
        """Test validating records that do not conform to the schema."""
        records = load_audit_records_from_json(audit_report_with_invalid_records)
        is_valid, errors = validate_audit_report_schema(records, schema_path)
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_with_missing_schema(self):
        """Test validation when schema file is missing."""
        valid_record = {"url": "test"}
        is_valid, errors = validate_audit_report_schema(
            [valid_record], Path("nonexistent_schema.yaml")
        )
        assert is_valid is False
        assert len(errors) == 1
        assert "not found" in errors[0].lower()


class TestRunSchemaValidation:
    def test_run_validation_on_valid_report(
        self,
        audit_report_with_valid_records: Path,
        schema_path: Path,
    ):
        """Test running validation on a valid report."""
        exit_code = run_schema_validation(
            audit_report_with_valid_records, schema_path, exit_on_failure=False
        )
        assert exit_code == 0

    def test_run_validation_on_invalid_report(
        self,
        audit_report_with_invalid_records: Path,
        schema_path: Path,
    ):
        """Test running validation on an invalid report."""
        exit_code = run_schema_validation(
            audit_report_with_invalid_records, schema_path, exit_on_failure=False
        )
        assert exit_code == 1

    def test_run_validation_on_nonexistent_report(self):
        """Test running validation on a nonexistent report."""
        exit_code = run_schema_validation(
            Path("nonexistent.json"), exit_on_failure=False
        )
        assert exit_code == 1
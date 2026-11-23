"""
Tests for data model schemas.
"""
import pytest
from datetime import datetime

from code.data_models.schemas import (
    validate_coverage_record,
    validate_aggregate_report,
    CoverageRecord,
    AggregateReport
)


class TestCoverageRecordValidation:
    def test_valid_coverage_record(self):
        """Test a valid coverage record passes validation."""
        record = {
            "run_id": "run_001",
            "dataset_id": "wine",
            "variable_name": "alcohol",
            "sample_size": 10,
            "confidence_level": 0.95,
            "replication_id": 1,
            "interval_type": "t_interval",
            "interval_lower": 12.5,
            "interval_upper": 13.5,
            "contains_mean": True,
            "population_mean": 13.0,
            "sample_mean": 13.1,
            "timestamp": datetime.now().isoformat()
        }
        assert validate_coverage_record(record) is True

    def test_missing_field_fails(self):
        """Test that missing required fields fail validation."""
        record = {
            "run_id": "run_001",
            # Missing dataset_id
            "variable_name": "alcohol",
            "sample_size": 10,
            "confidence_level": 0.95,
            "replication_id": 1,
            "interval_type": "t_interval",
            "interval_lower": 12.5,
            "interval_upper": 13.5,
            "contains_mean": True,
            "population_mean": 13.0,
            "sample_mean": 13.1,
            "timestamp": datetime.now().isoformat()
        }
        assert validate_coverage_record(record) is False

    def test_invalid_interval_type_fails(self):
        """Test that invalid interval_type fails validation."""
        record = {
            "run_id": "run_001",
            "dataset_id": "wine",
            "variable_name": "alcohol",
            "sample_size": 10,
            "confidence_level": 0.95,
            "replication_id": 1,
            "interval_type": "invalid_type",
            "interval_lower": 12.5,
            "interval_upper": 13.5,
            "contains_mean": True,
            "population_mean": 13.0,
            "sample_mean": 13.1,
            "timestamp": datetime.now().isoformat()
        }
        assert validate_coverage_record(record) is False

    def test_non_bool_contains_mean_fails(self):
        """Test that non-boolean contains_mean fails validation."""
        record = {
            "run_id": "run_001",
            "dataset_id": "wine",
            "variable_name": "alcohol",
            "sample_size": 10,
            "confidence_level": 0.95,
            "replication_id": 1,
            "interval_type": "t_interval",
            "interval_lower": 12.5,
            "interval_upper": 13.5,
            "contains_mean": "true",  # Should be bool
            "population_mean": 13.0,
            "sample_mean": 13.1,
            "timestamp": datetime.now().isoformat()
        }
        assert validate_coverage_record(record) is False

    def test_non_int_sample_size_fails(self):
        """Test that non-integer sample_size fails validation."""
        record = {
            "run_id": "run_001",
            "dataset_id": "wine",
            "variable_name": "alcohol",
            "sample_size": 10.5,  # Should be int
            "confidence_level": 0.95,
            "replication_id": 1,
            "interval_type": "t_interval",
            "interval_lower": 12.5,
            "interval_upper": 13.5,
            "contains_mean": True,
            "population_mean": 13.0,
            "sample_mean": 13.1,
            "timestamp": datetime.now().isoformat()
        }
        assert validate_coverage_record(record) is False


class TestAggregateReportValidation:
    def test_valid_aggregate_report(self):
        """Test a valid aggregate report passes validation."""
        report = {
            "report_id": "report_001",
            "generated_at": datetime.now().isoformat(),
            "total_datasets": 5,
            "total_replications": 5000,
            "summary": {
                "wine": {"t_interval": 0.94, "bootstrap": 0.93}
            }
        }
        assert validate_aggregate_report(report) is True

    def test_missing_required_field_fails(self):
        """Test that missing required fields fail validation."""
        report = {
            # Missing report_id
            "generated_at": datetime.now().isoformat(),
            "total_datasets": 5,
            "summary": {}
        }
        assert validate_aggregate_report(report) is False

    def test_non_int_total_datasets_fails(self):
        """Test that non-integer total_datasets fails validation."""
        report = {
            "report_id": "report_001",
            "generated_at": datetime.now().isoformat(),
            "total_datasets": 5.0,  # Should be int
            "summary": {}
        }
        assert validate_aggregate_report(report) is False

    def test_non_dict_summary_fails(self):
        """Test that non-dictionary summary fails validation."""
        report = {
            "report_id": "report_001",
            "generated_at": datetime.now().isoformat(),
            "total_datasets": 5,
            "summary": "not a dict"
        }
        assert validate_aggregate_report(report) is False

    def test_optional_fields_are_allowed(self):
        """Test that optional fields can be present without causing failure."""
        report = {
            "report_id": "report_001",
            "generated_at": datetime.now().isoformat(),
            "total_datasets": 5,
            "summary": {},
            "deviations": {"wine": {"t_interval": 0.01}},
            "bonferroni_corrected_pvalues": {"wine": {"t_interval": 0.04}},
            "practical_significance_flags": {"wine": {"t_interval": True}},
            "metadata": {"version": "1.0"}
        }
        assert validate_aggregate_report(report) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
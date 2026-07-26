import csv
import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test (assuming it's in the script we created)
# We will test the logic by creating a mock file and running the validation logic
# Since the script is standalone, we can import the logic or run it.
# For this test, we will simulate the validation logic directly.

from code.validate_correlation_schema import validate_row, load_schema

@pytest.fixture
def sample_schema():
    return load_schema(Path("contracts/correlation_result.schema.yaml"))

@pytest.fixture
def valid_row():
    return {
        "participant_id": "P001",
        "age": "65",
        "cognitive_score": "28",
        "cognitive_instrument": "MMSE",
        "global_efficiency": "0.45",
        "local_efficiency": "0.32",
        "characteristic_path_length": "2.2",
        "clustering_coefficient": "0.65",
        "modularity": "0.4",
        "age_correlation_rho": "-0.15",
        "age_correlation_pvalue": "0.04",
        "age_correlation_pvalue_adj": "0.08",
        "cognition_correlation_rho": "0.25",
        "cognition_correlation_pvalue": "0.02",
        "cognition_correlation_pvalue_adj": "0.04",
        "signal_quality_flag": "Good",
        "trace_id": "a" * 64
    }

@pytest.fixture
def invalid_row_missing_field():
    return {
        "participant_id": "P002",
        "age": "70",
        "cognitive_score": "25",
        # Missing cognitive_instrument
        "global_efficiency": "0.40",
        "local_efficiency": "0.30",
        "characteristic_path_length": "2.5",
        "clustering_coefficient": "0.60",
        "modularity": "0.35",
        "age_correlation_rho": "-0.20",
        "age_correlation_pvalue": "0.03",
        "age_correlation_pvalue_adj": "0.06",
        "cognition_correlation_rho": "0.30",
        "cognition_correlation_pvalue": "0.01",
        "cognition_correlation_pvalue_adj": "0.02",
        "signal_quality_flag": "Good",
        "trace_id": "b" * 64
    }

@pytest.fixture
def invalid_row_bad_trace_id():
    return {
        "participant_id": "P003",
        "age": "60",
        "cognitive_score": "29",
        "cognitive_instrument": "MoCA",
        "global_efficiency": "0.48",
        "local_efficiency": "0.35",
        "characteristic_path_length": "2.1",
        "clustering_coefficient": "0.68",
        "modularity": "0.42",
        "age_correlation_rho": "-0.10",
        "age_correlation_pvalue": "0.05",
        "age_correlation_pvalue_adj": "0.10",
        "cognition_correlation_rho": "0.20",
        "cognition_correlation_pvalue": "0.03",
        "cognition_correlation_pvalue_adj": "0.06",
        "signal_quality_flag": "Good",
        "trace_id": "short"
    }

@pytest.fixture
def invalid_row_bad_signal_quality():
    return {
        "participant_id": "P004",
        "age": "55",
        "cognitive_score": "27",
        "cognitive_instrument": "MMSE",
        "global_efficiency": "0.42",
        "local_efficiency": "0.31",
        "characteristic_path_length": "2.3",
        "clustering_coefficient": "0.62",
        "modularity": "0.38",
        "age_correlation_rho": "-0.18",
        "age_correlation_pvalue": "0.04",
        "age_correlation_pvalue_adj": "0.08",
        "cognition_correlation_rho": "0.22",
        "cognition_correlation_pvalue": "0.02",
        "cognition_correlation_pvalue_adj": "0.04",
        "signal_quality_flag": "Invalid Flag",
        "trace_id": "c" * 64
    }

def test_valid_row_validates_successfully(valid_row, sample_schema):
    errors = validate_row(valid_row, sample_schema)
    assert len(errors) == 0

def test_missing_required_field_fails(invalid_row_missing_field, sample_schema):
    errors = validate_row(invalid_row_missing_field, sample_schema)
    assert any("cognitive_instrument" in err for err in errors)

def test_bad_trace_id_format_fails(invalid_row_bad_trace_id, sample_schema):
    errors = validate_row(invalid_row_bad_trace_id, sample_schema)
    assert any("trace_id" in err for err in errors)

def test_bad_signal_quality_enum_fails(invalid_row_bad_signal_quality, sample_schema):
    errors = validate_row(invalid_row_bad_signal_quality, sample_schema)
    assert any("signal_quality_flag" in err for err in errors)

def test_null_cognitive_score_is_valid(sample_schema):
    row = {
        "participant_id": "P005",
        "age": "62",
        "cognitive_score": "",  # Empty string representing null
        "cognitive_instrument": "MMSE",
        "global_efficiency": "0.44",
        "local_efficiency": "0.33",
        "characteristic_path_length": "2.25",
        "clustering_coefficient": "0.64",
        "modularity": "0.39",
        "age_correlation_rho": "-0.12",
        "age_correlation_pvalue": "0.05",
        "age_correlation_pvalue_adj": "0.10",
        "cognition_correlation_rho": "0.24",
        "cognition_correlation_pvalue": "0.03",
        "cognition_correlation_pvalue_adj": "0.06",
        "signal_quality_flag": "Good",
        "trace_id": "d" * 64
    }
    errors = validate_row(row, sample_schema)
    assert len(errors) == 0
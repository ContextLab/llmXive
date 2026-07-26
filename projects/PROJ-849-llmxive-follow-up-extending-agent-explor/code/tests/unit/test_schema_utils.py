import pytest
from typing import List, Dict, Any
from tests.contract.test_simulation_schema import validate_simulation_record
from tests.contract.test_divergence_schema import validate_divergence_record
from tests.contract.test_correlation_schema import validate_correlation_report
from tests.contract.test_classifier_schema import validate_classifier_report

def test_validate_list_of_records_valid():
    records = [
        {"problem_id": "1", "simulated_failure": True, "failure_reason": "test"},
        {"problem_id": "2", "simulated_failure": False, "failure_reason": "ok"}
    ]
    for rec in records:
        assert validate_simulation_record(rec) is True

def test_validate_list_of_records_invalid():
    records = [
        {"problem_id": "1", "simulated_failure": True, "failure_reason": "test"},
        {"problem_id": "2"}  # Missing fields
    ]
    valid_count = 0
    for rec in records:
        if validate_simulation_record(rec):
            valid_count += 1
    assert valid_count == 1

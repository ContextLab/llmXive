import pytest
from code.utils.dataset_integrity import validate_record_fields, validate_dataset_records, IntegrityError
from pathlib import Path
import json

def test_validate_record_fields_missing():
    record = {"task_id": "1", "category": "Test"}
    required = {"task_id", "category", "constraint"}
    assert validate_record_fields(record, required) is False

def test_validate_record_fields_present():
    record = {"task_id": "1", "category": "Test", "constraint": "Must do X"}
    required = {"task_id", "category", "constraint"}
    assert validate_record_fields(record, required) is True

def test_validate_dataset_records_invalid():
    records = [
        {"task_id": "1", "category": "A", "constraint": "X"},
        {"task_id": "2", "category": "B"}, # Missing constraint
    ]
    required = {"task_id", "category", "constraint"}
    invalid = validate_dataset_records(records, required)
    assert len(invalid) == 1
    assert invalid[0]["record_id"] == "2"

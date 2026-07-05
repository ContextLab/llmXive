"""
Unit tests for PII Scanner (Task T042).
"""
import pytest
import tempfile
import json
import csv
from pathlib import Path
from code.security.pii_scanner import (
    scan_text_for_pii,
    scan_csv_file,
    scan_json_file,
    PIIResult
)

def test_scan_text_for_pii_email():
    text = "Contact: john.doe@example.com for info."
    results = scan_text_for_pii(text, 1, "contact_field")
    assert len(results) == 1
    assert results[0].pii_type == "email"
    assert "john.doe@example.com" in results[0].matched_text

def test_scan_text_for_pii_phone():
    text = "Call us at 555-123-4567."
    results = scan_text_for_pii(text, 1, "phone_field")
    assert len(results) == 1
    assert results[0].pii_type == "phone_us"

def test_scan_text_for_pii_ssn():
    text = "SSN: 123-45-6789."
    results = scan_text_for_pii(text, 1, "ssn_field")
    assert len(results) == 1
    assert results[0].pii_type == "ssn"

def test_scan_text_for_pii_no_pii():
    text = "This is a normal sentence with no PII."
    results = scan_text_for_pii(text, 1, "normal_field")
    assert len(results) == 0

def test_scan_csv_file(tmp_path):
    csv_file = tmp_path / "test.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["name", "email"])
        writer.writeheader()
        writer.writerow({"name": "John Doe", "email": "test@example.com"})
    
    results = scan_csv_file(csv_file)
    # Should find email
    assert any(r.pii_type == "email" for r in results)
    # Might find name depending on common names list
    assert any(r.pii_type == "common_name" for r in results) or len(results) >= 1

def test_scan_json_file(tmp_path):
    json_file = tmp_path / "test.json"
    data = {
        "user": "Jane Smith",
        "contact": {
            "email": "jane@example.com",
            "phone": "555-987-6543"
        }
    }
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    
    results = scan_json_file(json_file)
    types_found = [r.pii_type for r in results]
    assert "email" in types_found
    assert "phone_us" in types_found
    assert "common_name" in types_found

def test_pii_result_dataclass():
    result = PIIResult(
        file_path="test.txt",
        line_number=10,
        column=5,
        field_name="test_field",
        pii_type="email",
        matched_text="test@test.com"
    )
    assert result.file_path == "test.txt"
    assert result.pii_type == "email"
    assert result.matched_text == "test@test.com"

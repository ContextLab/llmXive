"""
Unit tests for the PII security scanning module.
"""
import pytest
import tempfile
import json
import csv
from pathlib import Path
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from security_scan import (
    scan_text_for_pii,
    scan_csv_file,
    scan_json_file,
    scan_yaml_file,
    is_valid_credit_card,
    PII_PATTERNS
)

def test_ssn_detection():
    """Test detection of US Social Security Numbers."""
    text = "Patient SSN: 123-45-6789 is admitted."
    findings = scan_text_for_pii(text)
    assert len(findings) == 1
    assert findings[0]["type"] == "ssn"
    assert findings[0]["value"] == "123-45-6789"

def test_email_detection():
    """Test detection of email addresses."""
    text = "Contact: researcher@example.com for details."
    findings = scan_text_for_pii(text)
    assert len(findings) == 1
    assert findings[0]["type"] == "email"
    assert findings[0]["value"] == "researcher@example.com"

def test_phone_detection():
    """Test detection of US phone numbers."""
    text = "Call us at (555) 123-4567 or 555-987-6543."
    findings = scan_text_for_pii(text)
    assert len(findings) == 2

def test_credit_card_invalid():
    """Test that invalid credit card numbers are ignored."""
    # Invalid Luhn checksum
    text = "Card: 1234-5678-9012-3456"
    findings = scan_text_for_pii(text)
    # Should find 0 because Luhn fails
    assert len(findings) == 0

def test_credit_card_valid():
    """Test that valid credit card numbers are detected."""
    # Valid Luhn checksum (test card number)
    text = "Card: 4532015112830366"
    findings = scan_text_for_pii(text)
    assert len(findings) == 1
    assert findings[0]["type"] == "credit_card"

def test_ip_address_detection():
    """Test detection of IP addresses."""
    text = "Server log from 192.168.1.1 shows activity."
    findings = scan_text_for_pii(text)
    assert len(findings) == 1
    assert findings[0]["type"] == "ip_address"

def test_csv_scanning():
    """Test scanning a CSV file for PII."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Email", "SSN"])
        writer.writerow(["John Doe", "john@example.com", "111-22-3333"])
        temp_path = Path(f.name)

    try:
        findings = scan_csv_file(temp_path)
        assert len(findings) == 2
        types = [f["type"] for f in findings]
        assert "email" in types
        assert "ssn" in types
    finally:
        temp_path.unlink()

def test_json_scanning():
    """Test scanning a JSON file for PII."""
    data = {
        "patient": "Jane Doe",
        "contact": "jane@example.com",
        "ssn": "999-88-7777"
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        temp_path = Path(f.name)

    try:
        findings = scan_json_file(temp_path)
        assert len(findings) == 2
    finally:
        temp_path.unlink()

def test_yaml_scanning():
    """Test scanning a YAML file for PII."""
    content = """
    patient:
      name: Bob Smith
      email: bob@test.org
      ssn: 444-55-6666
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)

    try:
        findings = scan_yaml_file(temp_path)
        assert len(findings) == 2
    finally:
        temp_path.unlink()

def test_clean_text():
    """Test that clean text returns no findings."""
    text = "This is a normal sentence with no sensitive data."
    findings = scan_text_for_pii(text)
    assert len(findings) == 0

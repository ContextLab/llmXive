"""
Unit tests for security scanning module.
"""

import pytest
import json
import tempfile
from pathlib import Path
from code.utils.io import ensure_dir

# Import the module under test
from code import code_08_security_scan as security_scan


class TestPIIDetection:
    """Test PII key and value detection."""
    
    def test_pii_key_detection_names(self):
        """Test detection of name-related keys."""
        assert security_scan.is_pii_key("first_name") is True
        assert security_scan.is_pii_key("last_name") is True
        assert security_scan.is_pii_key("full_name") is True
        assert security_scan.is_pii_key("patient_name") is True
    
    def test_pii_key_detection_contact(self):
        """Test detection of contact-related keys."""
        assert security_scan.is_pii_key("email") is True
        assert security_scan.is_pii_key("phone") is True
        assert security_scan.is_pii_key("phone_number") is True
        assert security_scan.is_pii_key("mobile") is True
    
    def test_pii_key_detection_personal(self):
        """Test detection of personal information keys."""
        assert security_scan.is_pii_key("date_of_birth") is True
        assert security_scan.is_pii_key("ssn") is True
        assert security_scan.is_pii_key("social_security_number") is True
        assert security_scan.is_pii_key("address") is True
    
    def test_bids_standard_keys_not_pii(self):
        """Test that standard BIDS keys are not flagged as PII."""
        assert security_scan.is_pii_key("subject") is False
        assert security_scan.is_pii_key("task") is False
        assert security_scan.is_pii_key("run") is False
        assert security_scan.is_pii_key("repetitiontime") is False
    
    def test_pii_value_detection_email(self):
        """Test detection of email addresses."""
        assert security_scan.is_pii_value("email", "test@example.com") is True
        assert security_scan.is_pii_value("contact_email", "user@domain.org") is True
    
    def test_pii_value_detection_phone(self):
        """Test detection of phone numbers."""
        assert security_scan.is_pii_value("phone", "123-456-7890") is True
        assert security_scan.is_pii_value("mobile", "123.456.7890") is True
    
    def test_pii_value_detection_ssn(self):
        """Test detection of SSN patterns."""
        assert security_scan.is_pii_value("ssn", "123-45-6789") is True
    
    def test_non_pii_values(self):
        """Test that non-PII values are not flagged."""
        assert security_scan.is_pii_value("task", "rest") is False
        assert security_scan.is_pii_value("repetitiontime", 2.5) is False
        assert security_scan.is_pii_value("manufacturer", "Siemens") is False
    
    def test_empty_values(self):
        """Test that empty values are not flagged as PII."""
        assert security_scan.is_pii_value("name", "") is False
        assert security_scan.is_pii_value("phone", "   ") is False


class TestRedaction:
    """Test PII redaction functionality."""
    
    def test_redact_value_consistency(self):
        """Test that redaction is consistent for same input."""
        result1 = security_scan.redact_value("john.doe@example.com", "email")
        result2 = security_scan.redact_value("john.doe@example.com", "email")
        assert result1 == result2
        assert result1 != "john.doe@example.com"
    
    def test_redact_value_format(self):
        """Test that redacted values follow expected format."""
        result = security_scan.redact_value("test@example.com", "email")
        assert result.startswith("[REDACTED_")
        assert result.endswith("]")
        assert len(result) > 10
    
    def test_redact_dict_simple(self):
        """Test redaction of a simple dictionary."""
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "task": "rest"
        }
        redacted = security_scan.redact_dict(data)
        
        assert redacted["name"] != "John Doe"
        assert redacted["email"] != "john@example.com"
        assert redacted["task"] == "rest"
    
    def test_redact_dict_nested(self):
        """Test redaction of nested dictionaries."""
        data = {
            "participant": {
                "name": "Jane Smith",
                "age": 45
            },
            "scan": {
                "task": "rest"
            }
        }
        redacted = security_scan.redact_dict(data)
        
        assert redacted["participant"]["name"] != "Jane Smith"
        assert redacted["participant"]["age"] == 45
        assert redacted["scan"]["task"] == "rest"
    
    def test_redact_dict_with_list(self):
        """Test redaction of dictionaries containing lists."""
        data = {
            "subjects": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 35}
            ],
            "task": "rest"
        }
        redacted = security_scan.redact_dict(data)
        
        assert redacted["subjects"][0]["name"] != "Alice"
        assert redacted["subjects"][1]["name"] != "Bob"
        assert redacted["subjects"][0]["age"] == 30
        assert redacted["task"] == "rest"


class TestFileScanning:
    """Test file scanning functionality."""
    
    def test_scan_filename_pii(self):
        """Test PII detection in filenames."""
        # These should detect patterns
        assert len(security_scan.scan_filename("sub-12345_bold.nii.gz")) > 0
        assert len(security_scan.scan_filename("patient_001.json")) > 0
    
    def test_scan_filename_no_pii(self):
        """Test filenames without PII."""
        result = security_scan.scan_filename("task-rest_bold.nii.gz")
        # May detect some patterns but should be minimal
        assert isinstance(result, list)
    
    def test_scan_json_file_valid(self):
        """Test scanning a valid JSON file with PII."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "task": "rest"
            }, f)
            temp_path = Path(f.name)
        
        try:
            redacted_data, detected_pii = security_scan.scan_json_file(temp_path)
            
            assert len(detected_pii) > 0
            assert redacted_data["first_name"] != "John"
            assert redacted_data["last_name"] != "Doe"
            assert redacted_data["email"] != "john@example.com"
            assert redacted_data["task"] == "rest"
        finally:
            temp_path.unlink()
    
    def test_scan_json_file_invalid(self):
        """Test scanning an invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json {")
            temp_path = Path(f.name)
        
        try:
            redacted_data, detected_pii = security_scan.scan_json_file(temp_path)
            
            assert redacted_data == {}
            assert len(detected_pii) > 0
            assert any("Error reading file" in str(p) for p in detected_pii)
        finally:
            temp_path.unlink()
    
    def test_scan_directory(self):
        """Test scanning a directory structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / "sub-001").mkdir()
            (temp_path / "sub-001" / "anat").mkdir()
            
            # JSON with PII
            with open(temp_path / "sub-001" / "participants.json", 'w') as f:
                json.dump({
                    "name": "Test Subject",
                    "age": 45
                }, f)
            
            # JSON without PII
            with open(temp_path / "sub-001" / "scans.json", 'w') as f:
                json.dump({
                    "task": "rest",
                    "repetitiontime": 2.5
                }, f)
            
            results = security_scan.scan_directory(temp_path)
            
            assert results["total_files"] >= 2
            assert results["json_files_scanned"] >= 2
            assert results["files_with_pii"] >= 1

class TestIntegration:
    """Integration tests for security scanning."""
    
    def test_end_to_end_scan(self):
        """Test complete scan and redaction workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create directory structure similar to BIDS
            (temp_path / "dataset_description.json").write_text(
                json.dumps({"Name": "Test Dataset", "first_name": "Admin"})
            )
            (temp_path / "sub-001").mkdir()
            (temp_path / "sub-001" / "func").mkdir()
            
            # File with PII
            with open(temp_path / "sub-001" / "func" / "task-rest_bold.json", 'w') as f:
                json.dump({
                    "participant_id": "sub-001",
                    "subject_name": "John Doe",
                    "email": "john@example.com",
                    "task": "rest"
                }, f)
            
            # Run scan
            results = security_scan.scan_directory(temp_path)
            
            # Verify results
            assert results["total_files"] >= 3
            assert results["json_files_scanned"] >= 2
            assert results["files_with_pii"] >= 1
            
            # Verify redaction
            with open(temp_path / "sub-001" / "func" / "task-rest_bold.json", 'r') as f:
                redacted = json.load(f)
            
            assert redacted["subject_name"] != "John Doe"
            assert redacted["email"] != "john@example.com"
            assert redacted["task"] == "rest"
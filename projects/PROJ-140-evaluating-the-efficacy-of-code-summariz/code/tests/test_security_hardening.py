import unittest
import os
import sys
import json
import csv
import tempfile
from pathlib import Path
from utils.security_hardening import (
    sanitize_value,
    sanitize_dict,
    sanitize_csv_file,
    sanitize_json_file,
    scan_directory_for_sensitive_data,
    enforce_data_protection_policy
)

class TestSanitizeValue(unittest.TestCase):
    def test_email_detection(self):
        self.assertEqual(sanitize_value("Contact: user@example.com"), "[REDACTED]")
    
    def test_ssn_detection(self):
        self.assertEqual(sanitize_value("SSN: 123-45-6789"), "[REDACTED]")
    
    def test_password_detection(self):
        self.assertEqual(sanitize_value("password=secret123"), "[REDACTED]")
    
    def test_clean_value(self):
        self.assertEqual(sanitize_value("Hello World"), "Hello World")
    
    def test_none_value(self):
        self.assertEqual(sanitize_value(None), "")

class TestSanitizeDict(unittest.TestCase):
    def test_nested_sensitive_data(self):
        data = {
            "user": "Alice",
            "details": {
                "email": "alice@test.com",
                "age": 30
            }
        }
        result = sanitize_dict(data)
        self.assertEqual(result["user"], "Alice")
        self.assertEqual(result["details"]["email"], "[REDACTED]")
        self.assertEqual(result["details"]["age"], "30")
    
    def test_sensitive_key_redaction(self):
        data = {
            "password": "12345",
            "username": "bob"
        }
        result = sanitize_dict(data)
        self.assertEqual(result["[REDACTED_KEY]"], "[REDACTED]")

class TestSanitizeCSVFile(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.input_file = os.path.join(self.temp_dir, "input.csv")
        self.output_file = os.path.join(self.temp_dir, "output.csv")
        
        with open(self.input_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["id", "email", "comment"])
            writer.writerow(["1", "user@example.com", "Normal comment"])
            writer.writerow(["2", "no_email", "Another comment"])
    
    def test_csv_sanitization(self):
        sanitize_csv_file(self.input_file, self.output_file)
        
        with open(self.output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(rows[0]["email"], "[REDACTED]")
        self.assertEqual(rows[1]["email"], "no_email")

class TestSanitizeInteractionLogs(unittest.TestCase):
    def test_directory_scan(self):
        temp_dir = tempfile.mkdtemp()
        output_dir = tempfile.mkdtemp()
        
        # Create a test file with sensitive data
        test_file = os.path.join(temp_dir, "test.json")
        with open(test_file, 'w') as f:
            json.dump({"email": "test@test.com", "safe": "data"}, f)
        
        # Run scan
        findings = scan_directory_for_sensitive_data(temp_dir)
        
        self.assertGreater(len(findings), 0)
        self.assertTrue(any("email" in str(f) for f in findings))

class TestScanDirectory(unittest.TestCase):
    def test_findings_structure(self):
        temp_dir = tempfile.mkdtemp()
        test_file = os.path.join(temp_dir, "log.txt")
        with open(test_file, 'w') as f:
            f.write("User email: admin@corp.com\n")
        
        findings = scan_directory_for_sensitive_data(temp_dir)
        self.assertEqual(len(findings), 1)
        self.assertTrue(any("admin@corp.com" in f["snippet"] for f in findings))

class TestEnforceDataProtectionPolicy(unittest.TestCase):
    def test_full_pipeline(self):
        input_dir = tempfile.mkdtemp()
        output_dir = tempfile.mkdtemp()
        
        # Create a CSV with sensitive data
        csv_path = os.path.join(input_dir, "logs.csv")
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["id", "email"])
            writer.writerow(["1", "secret@hidden.com"])
        
        success = enforce_data_protection_policy(input_dir, output_dir)
        
        self.assertTrue(success)
        
        # Verify output has redacted data
        out_path = os.path.join(output_dir, "sanitized_logs.csv")
        with open(out_path, 'r') as f:
            content = f.read()
        
        self.assertNotIn("secret@hidden.com", content)
        self.assertIn("[REDACTED]", content)

class TestIntegration(unittest.TestCase):
    def test_end_to_end_security(self):
        # Simulate a realistic log scenario
        temp_dir = tempfile.mkdtemp()
        output_dir = tempfile.mkdtemp()
        
        log_file = os.path.join(temp_dir, "interaction.log")
        with open(log_file, 'w') as f:
            f.write("User login: user@example.com\n")
            f.write("Session ID: 12345\n")
            f.write("Password attempt: wrong_pass\n")
        
        # Enforce policy
        result = enforce_data_protection_policy(temp_dir, output_dir)
        
        self.assertTrue(result)
        
        # Verify no leaks in output
        out_file = os.path.join(output_dir, "sanitized_interaction.log")
        with open(out_file, 'r') as f:
            content = f.read()
        
        self.assertNotIn("user@example.com", content)
        self.assertNotIn("wrong_pass", content)

if __name__ == '__main__':
    unittest.main()

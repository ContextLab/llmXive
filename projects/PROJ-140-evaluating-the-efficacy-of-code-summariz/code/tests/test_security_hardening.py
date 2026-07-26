"""
Unit tests for security hardening module.

Tests T042: Security hardening (ensure no sensitive data leaks in logs)
"""
import unittest
import os
import sys
import json
import csv
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.security_hardening import (
    sanitize_value,
    sanitize_dict,
    sanitize_csv_file,
    sanitize_json_file,
    sanitize_interaction_logs,
    scan_directory_for_sensitive_data,
    enforce_data_protection_policy,
    SENSITIVE_PATTERNS,
    REDACTION_STRING
)

class TestSanitizeValue(unittest.TestCase):
    """Test individual value sanitization."""
    
    def test_email_redaction(self):
        """Test email addresses are redacted."""
        test_value = "Contact: user@example.com for support"
        result = sanitize_value(test_value, 'email')
        self.assertEqual(result, f"Contact: {REDACTION_STRING} for support")
        
    def test_phone_redaction(self):
        """Test phone numbers are redacted."""
        test_value = "Call me at 555-123-4567"
        result = sanitize_value(test_value, 'phone')
        self.assertEqual(result, f"Call me at {REDACTION_STRING}")
        
    def test_ssn_redaction(self):
        """Test SSN is redacted."""
        test_value = "SSN: 123-45-6789"
        result = sanitize_value(test_value, 'ssn')
        self.assertEqual(result, f"SSN: {REDACTION_STRING}")
        
    def test_api_key_redaction(self):
        """Test API keys are redacted."""
        test_value = "api_key=abcdef1234567890abcdef1234567890"
        result = sanitize_value(test_value, 'api_key')
        self.assertIn(REDACTION_STRING, result)
        
    def test_no_redaction_for_safe_value(self):
        """Test that safe values pass through unchanged."""
        test_value = "This is a safe string with no sensitive data"
        result = sanitize_value(test_value)
        self.assertEqual(result, test_value)
        
    def test_non_string_input(self):
        """Test that non-string inputs are returned unchanged."""
        self.assertEqual(sanitize_value(123), 123)
        self.assertEqual(sanitize_value(None), None)
        
class TestSanitizeDict(unittest.TestCase):
    """Test dictionary sanitization."""
    
    def test_flat_dict_sanitization(self):
        """Test sanitization of flat dictionary."""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'safe_field': 'safe_value'
        }
        result = sanitize_dict(data)
        self.assertEqual(result['name'], 'John Doe')
        self.assertEqual(result['email'], REDACTION_STRING)
        self.assertEqual(result['safe_field'], 'safe_value')
        
    def test_nested_dict_sanitization(self):
        """Test sanitization of nested dictionaries."""
        data = {
            'user': {
                'email': 'nested@example.com',
                'profile': {
                    'phone': '123-456-7890'
                }
            }
        }
        result = sanitize_dict(data)
        self.assertEqual(result['user']['email'], REDACTION_STRING)
        self.assertEqual(result['user']['profile']['phone'], REDACTION_STRING)
        
    def test_list_in_dict_sanitization(self):
        """Test sanitization of lists within dictionaries."""
        data = {
            'contacts': ['user1@example.com', 'user2@example.com']
        }
        result = sanitize_dict(data)
        self.assertEqual(result['contacts'], [REDACTION_STRING, REDACTION_STRING])
        
class TestSanitizeCSVFile(unittest.TestCase):
    """Test CSV file sanitization."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_path = Path(self.temp_dir) / 'input.csv'
        self.output_path = Path(self.temp_dir) / 'output.csv'
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def test_csv_sanitization(self):
        """Test that CSV files are properly sanitized."""
        # Create test CSV
        with open(self.input_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'email', 'phone', 'safe'])
            writer.writerow(['1', 'test@example.com', '555-123-4567', 'safe_value'])
            
        # Sanitize
        counts = sanitize_csv_file(self.input_path, self.output_path)
        
        # Verify output
        with open(self.output_path, 'r') as f:
            reader = csv.DictReader(f)
            row = next(reader)
            
        self.assertEqual(row['id'], '1')
        self.assertEqual(row['email'], REDACTION_STRING)
        self.assertEqual(row['phone'], REDACTION_STRING)
        self.assertEqual(row['safe'], 'safe_value')
        
        # Verify counts
        self.assertGreater(counts['email'], 0)
        self.assertGreater(counts['phone'], 0)
        
class TestSanitizeInteractionLogs(unittest.TestCase):
    """Test interaction log sanitization specifically."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_path = Path(self.temp_dir) / 'raw_logs.csv'
        self.output_path = Path(self.temp_dir) / 'sanitized_logs.csv'
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def test_safe_fields_preserved(self):
        """Test that research-relevant fields are not redacted."""
        # Create test interaction log
        with open(self.input_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'participant_id', 'task_id', 'condition', 'timestamp_ms',
                'selected_line', 'ground_truth_line', 'notes'
            ])
            writer.writerow([
                'P001', 'T001', 'baseline', '1234567890',
                '42', '45', 'User found the bug quickly'
            ])
            
        # Sanitize
        sanitize_interaction_logs(self.input_path, self.output_path)
        
        # Verify safe fields are preserved
        with open(self.output_path, 'r') as f:
            reader = csv.DictReader(f)
            row = next(reader)
            
        self.assertEqual(row['participant_id'], 'P001')
        self.assertEqual(row['task_id'], 'T001')
        self.assertEqual(row['timestamp_ms'], '1234567890')
        self.assertEqual(row['selected_line'], '42')
        
    def test_sensitive_data_in_notes_redacted(self):
        """Test that sensitive data in notes field is redacted."""
        with open(self.input_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['participant_id', 'notes'])
            writer.writerow(['P001', 'Contact me at user@example.com'])
            
        sanitize_interaction_logs(self.input_path, self.output_path)
        
        with open(self.output_path, 'r') as f:
            reader = csv.DictReader(f)
            row = next(reader)
            
        self.assertEqual(row['notes'], f'Contact me at {REDACTION_STRING}')
        
class TestScanDirectory(unittest.TestCase):
    """Test directory scanning for sensitive data."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / 'test.txt'
        
        # Create file with sensitive data
        with open(self.test_file, 'w') as f:
            f.write('Contact: user@example.com\nPhone: 555-123-4567\n')
            
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def test_scan_detects_sensitive_data(self):
        """Test that scanning detects sensitive data."""
        results = scan_directory_for_sensitive_data(self.temp_dir)
        
        self.assertEqual(results['files_scanned'], 1)
        self.assertEqual(results['files_with_sensitive_data'], 1)
        self.assertEqual(len(results['findings']), 1)
        
    def test_scan_report_output(self):
        """Test that scan can write a report."""
        report_path = Path(self.temp_dir) / 'report.json'
        results = scan_directory_for_sensitive_data(self.temp_dir, report_path)
        
        self.assertTrue(report_path.exists())
        with open(report_path, 'r') as f:
            report = json.load(f)
        self.assertEqual(report['files_with_sensitive_data'], 1)
        
class TestEnforceDataProtectionPolicy(unittest.TestCase):
    """Test comprehensive data protection enforcement."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = Path(self.temp_dir) / 'input'
        self.output_dir = Path(self.temp_dir) / 'output'
        self.consent_dir = Path(self.temp_dir) / 'consent'
        
        self.input_dir.mkdir()
        self.consent_dir.mkdir()
        
        # Create test files
        with open(self.input_dir / 'logs.csv', 'w') as f:
            f.write('id,email\n1,test@example.com\n')
            
        with open(self.consent_dir / 'consent.csv', 'w') as f:
            f.write('participant,ssn\nP001,123-45-6789\n')
            
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def test_consents_excluded(self):
        """Test that consent files are excluded from processing."""
        actions = enforce_data_protection_policy(
            self.input_dir, self.output_dir, self.consent_dir
        )
        
        self.assertGreater(actions['consent_files_excluded'], 0)
        self.assertTrue((self.output_dir / 'logs.csv').exists())
        self.assertFalse((self.output_dir / 'consent' / 'consent.csv').exists())
        
    def test_output_files_sanitized(self):
        """Test that output files are properly sanitized."""
        actions = enforce_data_protection_policy(
            self.input_dir, self.output_dir, self.consent_dir
        )
        
        self.assertGreater(actions['files_sanitized'], 0)
        self.assertGreater(actions['sensitive_patterns_found'], 0)
        
class TestIntegration(unittest.TestCase):
    """Integration tests for security hardening."""
    
    def test_end_to_end_log_sanitization(self):
        """Test complete flow of log sanitization."""
        temp_dir = tempfile.mkdtemp()
        try:
            input_path = Path(temp_dir) / 'raw_logs.csv'
            output_path = Path(temp_dir) / 'sanitized_logs.csv'
            
            # Create realistic interaction log
            with open(input_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'participant_id', 'task_id', 'email', 'phone',
                    'timestamp_ms', 'selected_line'
                ])
                writer.writerow([
                    'P001', 'T001', 'participant@example.com', '555-123-4567',
                    '1234567890', '42'
                ])
                
            # Sanitize
            counts = sanitize_interaction_logs(input_path, output_path)
            
            # Verify
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                row = next(reader)
                
            self.assertEqual(row['participant_id'], 'P001')
            self.assertEqual(row['task_id'], 'T001')
            self.assertEqual(row['timestamp_ms'], '1234567890')
            self.assertEqual(row['selected_line'], '42')
            self.assertEqual(row['email'], REDACTION_STRING)
            self.assertEqual(row['phone'], REDACTION_STRING)
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)

if __name__ == '__main__':
    unittest.main()
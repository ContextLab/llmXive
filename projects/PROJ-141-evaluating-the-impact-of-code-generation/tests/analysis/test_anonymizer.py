"""
Tests for the anonymization module.
"""
import pytest
import sys
import os
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.anonymizer import (
    anonymize_record,
    anonymize_dataset,
    generate_anonymous_id,
    is_pii_field,
    detect_pii_value,
    get_anonymization_report
)

class TestAnonymization:
    """Test cases for anonymization functionality."""

    def test_remove_pii_name(self):
        """Test that name field is removed."""
        record = {
            'participant_id': 'P-123',
            'name': 'John Doe',
            'age': 25
        }
        anonymized = anonymize_record(record)
        
        assert 'name' not in anonymized
        assert 'participant_id' not in anonymized
        assert 'anonymous_id' in anonymized
        assert anonymized['age'] == 25

    def test_remove_pii_email(self):
        """Test that email field is removed."""
        record = {
            'id': 'P-456',
            'email': 'test@example.com',
            'experience': 3
        }
        anonymized = anonymize_record(record)
        
        assert 'email' not in anonymized
        assert 'anonymous_id' in anonymized

    def test_remove_pii_ip(self):
        """Test that IP address field is removed."""
        record = {
            'participant_id': 'P-789',
            'ip_address': '192.168.1.1',
            'session_duration': 300
        }
        anonymized = anonymize_record(record)
        
        assert 'ip_address' not in anonymized
        assert 'anonymous_id' in anonymized

    def test_detect_email_in_value(self):
        """Test detection of email patterns in values."""
        assert detect_pii_value('test@example.com') is True
        assert detect_pii_value('not an email') is False
        assert detect_pii_value('192.168.1.1') is True  # IP pattern
        assert detect_pii_value('+1-555-123-4567') is True  # Phone pattern

    def test_anonymous_id_deterministic(self):
        """Test that anonymous ID generation is deterministic."""
        id1 = generate_anonymous_id('P-123')
        id2 = generate_anonymous_id('P-123')
        
        assert id1 == id2
        assert len(id1) == 64  # SHA-256 hex length
        assert id1 != 'P-123'  # Not the same as original

    def test_anonymous_id_with_salt(self):
        """Test that salt affects anonymous ID generation."""
        id1 = generate_anonymous_id('P-123', salt='salt1')
        id2 = generate_anonymous_id('P-123', salt='salt2')
        
        assert id1 != id2

    def test_anonymize_dataset(self):
        """Test anonymization of multiple records."""
        records = [
            {'id': 'P-1', 'name': 'Alice', 'age': 20},
            {'id': 'P-2', 'email': 'bob@test.com', 'age': 25}
        ]
        anonymized = anonymize_dataset(records)
        
        assert len(anonymized) == 2
        assert 'name' not in anonymized[0]
        assert 'email' not in anonymized[1]
        assert 'anonymous_id' in anonymized[0]
        assert 'anonymous_id' in anonymized[1]

    def test_non_dict_record_raises(self):
        """Test that non-dict records raise TypeError."""
        with pytest.raises(TypeError):
            anonymize_record("not a dict")

    def test_report_generation(self):
        """Test anonymization report generation."""
        original = {
            'id': 'P-123',
            'name': 'John',
            'age': 30
        }
        anonymized = anonymize_record(original)
        report = get_anonymization_report(original, anonymized)
        
        assert 'removed_fields' in report
        assert 'name' in report['removed_fields']
        assert 'transformed_fields' in report
        assert report['total_fields_original'] == 3
        assert report['total_fields_anonymized'] == 2

if __name__ == '__main__':
    pytest.main([__file__, '-v'])

"""
Tests for T012c: Generate static test fixture from real data.
"""
import json
import os
from pathlib import Path
import pytest

from config import get_path
from utils import load_json_file


class TestStaticTestFixture:
    """Test cases for the static test fixture generation."""
    
    @pytest.fixture
    def fixture_path(self):
        """Return the path to the static test fixture."""
        return Path(get_path('data/test_static_logs.json'))
    
    def test_fixture_file_exists(self, fixture_path):
        """Test that the fixture file exists."""
        assert fixture_path.exists(), f"Fixture file does not exist: {fixture_path}"
    
    def test_fixture_is_valid_json(self, fixture_path):
        """Test that the fixture is valid JSON."""
        try:
            with open(fixture_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            assert isinstance(data, list), "Fixture should be a list"
        except json.JSONDecodeError as e:
            pytest.fail(f"Fixture is not valid JSON: {e}")
    
    def test_fixture_has_required_fields(self, fixture_path):
        """Test that all records have required fields: log_id, text, label, timestamp."""
        data = load_json_file(fixture_path)
        
        required_fields = {'log_id', 'text', 'label', 'timestamp'}
        
        for i, record in enumerate(data):
            missing = required_fields - set(record.keys())
            assert not missing, f"Record {i} missing fields: {missing}"
    
    def test_fixture_has_data(self, fixture_path):
        """Test that the fixture contains at least some records."""
        data = load_json_file(fixture_path)
        assert len(data) > 0, "Fixture should contain at least one record"
    
    def test_fixture_contains_malicious_and_benign(self, fixture_path):
        """Test that the fixture contains both malicious and benign labels."""
        data = load_json_file(fixture_path)
        
        labels = {record['label'] for record in data}
        assert 'malicious' in labels, "Fixture should contain malicious records"
        assert 'benign' in labels, "Fixture should contain benign records"
    
    def test_log_ids_are_unique(self, fixture_path):
        """Test that all log_ids are unique."""
        data = load_json_file(fixture_path)
        log_ids = [record['log_id'] for record in data]
        assert len(log_ids) == len(set(log_ids)), "All log_ids should be unique"
    
    def test_text_fields_are_non_empty(self, fixture_path):
        """Test that all text fields are non-empty strings."""
        data = load_json_file(fixture_path)
        
        for i, record in enumerate(data):
            text = record['text']
            assert isinstance(text, str), f"Record {i} text should be a string"
            assert len(text.strip()) > 0, f"Record {i} text should not be empty"
    
    def test_timestamps_are_valid(self, fixture_path):
        """Test that timestamps are present and non-empty."""
        data = load_json_file(fixture_path)
        
        for i, record in enumerate(data):
            timestamp = record['timestamp']
            assert timestamp is not None, f"Record {i} timestamp should not be None"
            assert str(timestamp).strip() != '', f"Record {i} timestamp should not be empty"
    
    def test_fixture_loads_via_utils(self, fixture_path):
        """Test that the fixture can be loaded using utils.load_json_file."""
        try:
            data = load_json_file(fixture_path)
            assert isinstance(data, list)
            assert len(data) > 0
        except Exception as e:
            pytest.fail(f"Failed to load fixture via utils: {e}")
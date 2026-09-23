"""
Unit tests for mock data generation.
"""
import pytest
import os
import sys
import csv
from pathlib import Path
import hashlib

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.generate_mock_data import (
    generate_ip,
    generate_session_id,
    generate_timestamp,
    generate_user_agent,
    generate_mock_data,
    get_submissions_csv_path,
    compute_sha256_checksum
)

class TestMockDataGeneration:
    """Tests for mock data generation functions."""

    def test_generate_ip_format(self):
        """Test that generated IP addresses have valid format."""
        ip = generate_ip()
        parts = ip.split('.')
        assert len(parts) == 4
        assert all(0 <= int(part) <= 255 for part in parts)

    def test_generate_session_id_uniqueness(self):
        """Test that generated session IDs are unique."""
        ids = [generate_session_id() for _ in range(100)]
        assert len(set(ids)) == 100

    def test_generate_user_agent_not_empty(self):
        """Test that generated user agents are non-empty strings."""
        ua = generate_user_agent()
        assert isinstance(ua, str)
        assert len(ua) > 0
        assert "Mozilla" in ua

    def test_generate_mock_data_structure(self):
        """Test that mock data has the correct structure."""
        data = generate_mock_data()
        
        assert len(data) == 250
        
        # Check first row structure
        first_row = data[0]
        required_fields = [
            'participant_id', 'stimulus_id', 'credibility', 'professionalism',
            'timestamp', 'hashed_ip', 'age', 'education', 'user_agent',
            'duplicate_flag', 'session_status', 'submission_status'
        ]
        
        for field in required_fields:
            assert field in first_row, f"Missing field: {field}"

    def test_generate_mock_data_ratings_range(self):
        """Test that generated ratings are within valid range (1-5)."""
        data = generate_mock_data()
        
        for row in data:
            credibility = float(row['credibility'])
            professionalism = float(row['professionalism'])
            
            assert 1 <= credibility <= 5, f"Credibility out of range: {credibility}"
            assert 1 <= professionalism <= 5, f"Professionalism out of range: {professionalism}"

    def test_generate_mock_data_user_agent_truncation(self):
        """Test that user agents are truncated to 255 characters."""
        data = generate_mock_data()
        
        for row in data:
            assert len(row['user_agent']) <= 255, "User agent exceeds 255 characters"

    def test_csv_write_and_read(self):
        """Test that the generated CSV can be written and read back correctly."""
        # Generate and write data
        data = generate_mock_data()
        csv_path = get_submissions_csv_path()
        
        # Write to CSV
        import csv as csv_module
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = data[0].keys()
        
        with open(csv_path, 'w', newline='') as f:
            writer = csv_module.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        # Read back
        with open(csv_path, 'r', newline='') as f:
            reader = csv_module.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 250
        
        # Verify a few fields
        assert rows[0]['participant_id'] != ''
        assert rows[0]['stimulus_id'] in ['Professional', 'Minimalist', 'Low-Quality', 'Neutral']

    def test_checksum_computation(self):
        """Test that checksum computation works correctly."""
        # Create a temporary file
        test_path = Path('/tmp/test_checksum.csv')
        test_path.write_text("test,data\n1,2\n3,4")
        
        checksum = compute_sha256_checksum(test_path)
        
        # Verify it's a valid SHA-256 hash
        assert len(checksum) == 64
        assert all(c in '0123456789abcdef' for c in checksum)
        
        # Clean up
        test_path.unlink()
"""
Unit tests for T022e: Capture demographic data functionality.
"""
import pytest
import os
import csv
import tempfile
from pathlib import Path
from datetime import datetime
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.helpers import (
    prepare_submission_row, 
    append_to_submissions_csv,
    save_submission,
    get_project_root,
    get_submissions_csv_path
)

class TestCaptureData:
    """Tests for demographic data capture functionality."""

    def test_prepare_submission_row_structure(self):
        """Test that prepare_submission_row creates the correct dictionary structure."""
        row = prepare_submission_row(
            participant_id="test-uuid-123",
            stimulus_id="Professional",
            credibility=5,
            professionalism=6,
            timestamp="2024-01-01T12:00:00",
            hashed_ip="abc123hash",
            age=25,
            education="Bachelor's Degree",
            user_agent="Mozilla/5.0",
            duplicate_flag="NO",
            session_status="active",
            submission_status="complete"
        )
        
        expected_keys = [
            'participant_id', 'stimulus_id', 'credibility', 'professionalism',
            'timestamp', 'hashed_ip', 'age', 'education', 'user_agent',
            'duplicate_flag', 'session_status', 'submission_status'
        ]
        
        assert all(key in row for key in expected_keys)
        assert row['participant_id'] == "test-uuid-123"
        assert row['age'] == 25
        assert row['education'] == "Bachelor's Degree"

    def test_append_to_submissions_csv_creates_file(self):
        """Test that append_to_submissions_csv creates the file if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_csv = Path(tmpdir) / "test_submissions.csv"
            
            # Create a test row
            row = prepare_submission_row(
                participant_id="test-uuid-123",
                stimulus_id="Professional",
                credibility=5,
                professionalism=6,
                timestamp="2024-01-01T12:00:00",
                hashed_ip="abc123hash",
                age=25,
                education="Bachelor's Degree",
                user_agent="Mozilla/5.0",
                duplicate_flag="NO",
                session_status="active",
                submission_status="complete"
            )
            
            # Append to the file
            append_to_submissions_csv(row, test_csv)
            
            # Verify file exists
            assert test_csv.exists()
            
            # Verify content
            with open(test_csv, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            assert len(rows) == 1
            assert rows[0]['participant_id'] == "test-uuid-123"
            assert rows[0]['age'] == "25"
            assert rows[0]['education'] == "Bachelor's Degree"

    def test_append_to_submissions_csv_appends_data(self):
        """Test that append_to_submissions_csv appends to existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_csv = Path(tmpdir) / "test_submissions.csv"
            
            # Create initial file with header
            with open(test_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'participant_id', 'stimulus_id', 'credibility', 'professionalism',
                    'timestamp', 'hashed_ip', 'age', 'education', 'user_agent',
                    'duplicate_flag', 'session_status', 'submission_status'
                ])
                writer.writeheader()
            
            # Add first row
            row1 = prepare_submission_row(
                participant_id="uuid-1",
                stimulus_id="Professional",
                credibility=5,
                professionalism=6,
                timestamp="2024-01-01T12:00:00",
                hashed_ip="hash1",
                age=25,
                education="Bachelor's Degree",
                user_agent="Mozilla/5.0",
                duplicate_flag="NO",
                session_status="active",
                submission_status="complete"
            )
            append_to_submissions_csv(row1, test_csv)
            
            # Add second row
            row2 = prepare_submission_row(
                participant_id="uuid-2",
                stimulus_id="Minimalist",
                credibility=4,
                professionalism=5,
                timestamp="2024-01-01T12:05:00",
                hashed_ip="hash2",
                age=30,
                education="Master's Degree",
                user_agent="Chrome/100",
                duplicate_flag="NO",
                session_status="active",
                submission_status="complete"
            )
            append_to_submissions_csv(row2, test_csv)
            
            # Verify both rows exist
            with open(test_csv, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            assert len(rows) == 2
            assert rows[0]['participant_id'] == "uuid-1"
            assert rows[1]['participant_id'] == "uuid-2"
            assert rows[1]['age'] == "30"

    def test_save_submission_integration(self):
        """Test the full save_submission flow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock the get_submissions_csv_path to use temp dir
            import utils.helpers
            original_func = utils.helpers.get_submissions_csv_path
            utils.helpers.get_submissions_csv_path = lambda: Path(tmpdir) / "submissions.csv"
            
            try:
                save_submission(
                    participant_id="integration-test-uuid",
                    stimulus_id="Low-Quality",
                    credibility=3,
                    professionalism=2,
                    timestamp="2024-01-01T13:00:00",
                    hashed_ip="integration-hash",
                    age=40,
                    education="Some College",
                    user_agent="Safari/15",
                    duplicate_flag="NO",
                    session_status="active",
                    submission_status="complete"
                )
                
                csv_path = Path(tmpdir) / "submissions.csv"
                assert csv_path.exists()
                
                with open(csv_path, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    
                assert len(rows) == 1
                assert rows[0]['participant_id'] == "integration-test-uuid"
                assert rows[0]['age'] == "40"
                assert rows[0]['education'] == "Some College"
                assert rows[0]['stimulus_id'] == "Low-Quality"
            finally:
                # Restore original function
                utils.helpers.get_submissions_csv_path = original_func

    def test_demographic_fields_in_csv(self):
        """Test that demographic fields (age, education) are correctly captured."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_csv = Path(tmpdir) / "test_submissions.csv"
            
            row = prepare_submission_row(
                participant_id="demo-test",
                stimulus_id="Neutral",
                credibility=4,
                professionalism=4,
                timestamp="2024-01-01T14:00:00",
                hashed_ip="demo-hash",
                age=22,
                education="High School Diploma",
                user_agent="Firefox/90",
                duplicate_flag="NO",
                session_status="active",
                submission_status="complete"
            )
            
            append_to_submissions_csv(row, test_csv)
            
            with open(test_csv, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            assert rows[0]['age'] == "22"
            assert rows[0]['education'] == "High School Diploma"
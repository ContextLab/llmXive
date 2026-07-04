"""
Unit tests for the Controlled Data Collection Protocol (T012c).
"""
import os
import sys
import pytest
import pandas as pd
import tempfile
import json
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.data_collection import ConsentManager, AnonymizationPipeline, run_collection_protocol
from code.logging_config import setup_logging

@pytest.fixture(autouse=True)
def setup_logging_fixture():
    setup_logging()

class TestConsentManager:
    def test_form_version_hash(self):
        """Test that the consent form version is a valid hash."""
        manager = ConsentManager()
        assert isinstance(manager.form_version, str)
        assert len(manager.form_version) == 12  # Truncated SHA-256

    def test_capture_consent_granted(self):
        """Test consent capture when signed."""
        manager = ConsentManager()
        record = manager.capture_consent(participant_id="P123", signed=True)
        
        assert record["consent_status"] == "granted"
        assert record["participant_id"] == "P123"
        assert "timestamp" in record
        assert "form_version" in record

    def test_capture_consent_denied(self):
        """Test consent capture when not signed."""
        manager = ConsentManager()
        record = manager.capture_consent(participant_id="P123", signed=False)
        
        assert record["consent_status"] == "denied"

class TestAnonymizationPipeline:
    def test_anonymize_id_deterministic(self):
        """Test that anonymization is deterministic for the same input."""
        pipeline = AnonymizationPipeline(salt="test_salt_123")
        id1 = pipeline.anonymize_id("user@example.com")
        id2 = pipeline.anonymize_id("user@example.com")
        assert id1 == id2
        assert len(id1) == 16

    def test_process_record_removes_pii(self):
        """Test that PII fields are handled correctly."""
        pipeline = AnonymizationPipeline(salt="test_salt")
        raw_record = {
            "email": "user@example.com",
            "full_name": "John Doe",
            "age": 30,
            "score": 0.85
        }
        anon_record = pipeline.process_record(raw_record)
        
        # PII fields should be anonymized or removed
        assert "email" in anon_record # Should be hashed
        assert anon_record["email"] != "user@example.com"
        assert "age" in anon_record
        assert "score" in anon_record

    def test_process_dataframe(self):
        """Test processing a full DataFrame."""
        pipeline = AnonymizationPipeline(salt="test_salt")
        data = {
            "email": ["a@b.com", "c@d.com"],
            "value": [1, 2]
        }
        df = pd.DataFrame(data)
        
        result_df = pipeline.process_dataframe(df)
        
        assert len(result_df) == 2
        assert result_df["email"].iloc[0] != "a@b.com"

class TestRunCollectionProtocol:
    def test_missing_input_file(self, caplog):
        """Test behavior when input file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.csv")
            run_collection_protocol(input_file="nonexistent.csv", output_file=output_path)
            # Should not crash, just log warning/info
            assert "No input file provided" in caplog.text or "Processing input file" not in caplog.text

    def test_process_csv_roundtrip(self):
        """Test processing a CSV file from input to output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.csv")
            output_path = os.path.join(tmpdir, "output.csv")
            
            # Create dummy input
            df_in = pd.DataFrame({"email": ["test@test.com"], "score": [0.9]})
            df_in.to_csv(input_path, index=False)
            
            # Run protocol
            run_collection_protocol(input_file=input_path, output_file=output_path)
            
            # Verify output exists
            assert os.path.exists(output_path)
            
            # Verify content
            df_out = pd.read_csv(output_path)
            assert len(df_out) == 1
            assert df_out["email"].iloc[0] != "test@test.com" # Anonymized
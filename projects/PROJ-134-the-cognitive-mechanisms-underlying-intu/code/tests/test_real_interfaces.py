"""
Unit tests for Real Data Architecture Interfaces.

This module verifies that the constants defined in code/data/ingest_real.py
match the expected canonical values and schemas required for real data ingestion.

Dependencies:
- T050: code/data/ingest_real.py (Interface Definition)
"""

import pytest
import sys
from pathlib import Path

# Ensure the code directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.ingest_real import (
    OSF_API_URL,
    HF_DATASET_ID,
    VR_LOG_SCHEMA_COLUMNS,
    DataFetchError,
    SchemaError
)

class TestOSFAPIURL:
    """Tests for the OSF API URL constant."""
    
    def test_osf_api_url_exists(self):
        """Assert that OSF_API_URL is defined and not None."""
        assert OSF_API_URL is not None, "OSF_API_URL must be defined"
        assert isinstance(OSF_API_URL, str), "OSF_API_URL must be a string"
        assert len(OSF_API_URL) > 0, "OSF_API_URL must not be empty"
    
    def test_osf_api_url_canonical(self):
        """Assert that OSF_API_URL matches the expected canonical OSF base URL."""
        expected_url = "https://api.osf.io/v2"
        assert OSF_API_URL == expected_url, (
            f"OSF_API_URL mismatch. Expected '{expected_url}', got '{OSF_API_URL}'"
        )
    
    def test_osf_api_url_protocol(self):
        """Assert that OSF_API_URL uses HTTPS."""
        assert OSF_API_URL.startswith("https://"), (
            f"OSF_API_URL must use HTTPS protocol. Got: {OSF_API_URL}"
        )

class TestHuggingFaceDatasetID:
    """Tests for the HuggingFace Dataset ID constant."""
    
    def test_hf_dataset_id_exists(self):
        """Assert that HF_DATASET_ID is defined and not None."""
        assert HF_DATASET_ID is not None, "HF_DATASET_ID must be defined"
        assert isinstance(HF_DATASET_ID, str), "HF_DATASET_ID must be a string"
        assert len(HF_DATASET_ID) > 0, "HF_DATASET_ID must not be empty"
    
    def test_hf_dataset_id_format(self):
        """Assert that HF_DATASET_ID follows the 'username/dataset_name' format."""
        assert "/" in HF_DATASET_ID, (
            f"HF_DATASET_ID must contain a '/' separator. Got: {HF_DATASET_ID}"
        )
        parts = HF_DATASET_ID.split("/")
        assert len(parts) == 2, (
            f"HF_DATASET_ID must have exactly two parts (user/dataset). Got: {HF_DATASET_ID}"
        )
        assert len(parts[0]) > 0, "HF_DATASET_ID username part must not be empty"
        assert len(parts[1]) > 0, "HF_DATASET_ID dataset name part must not be empty"
    
    def test_hf_dataset_id_canonical(self):
        """Assert that HF_DATASET_ID matches the expected canonical dataset ID."""
        # The canonical dataset for Moral Stories in this project context
        expected_id = "llmXive/moral-stories-v1"
        assert HF_DATASET_ID == expected_id, (
            f"HF_DATASET_ID mismatch. Expected '{expected_id}', got '{HF_DATASET_ID}'"
        )

class TestVRLogSchemaColumns:
    """Tests for the VR Log Schema Columns constant."""
    
    def test_vr_log_schema_columns_exists(self):
        """Assert that VR_LOG_SCHEMA_COLUMNS is defined and not None."""
        assert VR_LOG_SCHEMA_COLUMNS is not None, "VR_LOG_SCHEMA_COLUMNS must be defined"
        assert isinstance(VR_LOG_SCHEMA_COLUMNS, (list, tuple)), (
            "VR_LOG_SCHEMA_COLUMNS must be a list or tuple"
        )
    
    def test_vr_log_schema_columns_required_fields(self):
        """Assert that VR_LOG_SCHEMA_COLUMNS contains all required columns."""
        required_columns = {
            "response_time",
            "gaze_x",
            "gaze_y",
            "judgment_rating"
        }
        
        actual_columns = set(VR_LOG_SCHEMA_COLUMNS)
        
        missing_columns = required_columns - actual_columns
        
        assert not missing_columns, (
            f"VR_LOG_SCHEMA_COLUMNS is missing required columns: {missing_columns}. "
            f"Current columns: {VR_LOG_SCHEMA_COLUMNS}"
        )
    
    def test_vr_log_schema_columns_types(self):
        """Assert that all items in VR_LOG_SCHEMA_COLUMNS are strings."""
        for col in VR_LOG_SCHEMA_COLUMNS:
            assert isinstance(col, str), (
                f"VR_LOG_SCHEMA_COLUMNS item '{col}' must be a string. Got {type(col)}"
            )

class TestInterfaceConstantsIntegrity:
    """Additional integrity checks for the interface constants."""
    
    def test_no_empty_strings_in_columns(self):
        """Assert that no column name in VR_LOG_SCHEMA_COLUMNS is an empty string."""
        for col in VR_LOG_SCHEMA_COLUMNS:
            assert col.strip() != "", f"VR_LOG_SCHEMA_COLUMNS contains empty string: '{col}'"
    
    def test_osf_url_no_trailing_slash(self):
        """Assert that OSF_API_URL does not end with a trailing slash."""
        assert not OSF_API_URL.endswith("/"), (
            f"OSF_API_URL should not end with a trailing slash. Got: {OSF_API_URL}"
        )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

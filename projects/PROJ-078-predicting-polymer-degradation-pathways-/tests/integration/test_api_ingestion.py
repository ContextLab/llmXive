"""
Integration tests for API ingestion with rate-limit backoff.

Tests the full ingestion pipeline including rate limiting behavior.
"""

import pytest
from unittest.mock import patch, MagicMock, call
import time
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.ingest import download_records_from_nist
from code.utils import retry_with_backoff

class TestAPIIngestionWithBackoff:
    """Integration tests for API ingestion with rate-limit backoff."""
    
    @patch('code.ingest._fetch_nist_record')
    @patch('code.ingest.time.sleep')
    def test_backoff_on_rate_limit(self, mock_sleep, mock_fetch):
        """Test that backoff is applied on rate limit errors."""
        # Simulate rate limit errors followed by success
        mock_fetch.side_effect = [
            Exception("429 Too Many Requests"),
            Exception("429 Too Many Requests"),
            {
                "smiles": "CCO",
                "degradation_pathway": "hydrolysis",
                "temperature": 25.0,
                "ph": 7.0,
                "uv_intensity": None,
                "other_conditions": {},
                "metadata": {}
            }
        ]
        
        from code.ingest import MAX_RETRIES, RATE_LIMIT_DELAY
        
        # This will fail because we're mocking but it tests the backoff logic
        with pytest.raises(RuntimeError):
            download_records_from_nist(material_ids=["test-id"])
        
        # Verify sleep was called for backoff
        assert mock_sleep.call_count >= 1
    
    @patch('code.ingest._fetch_nist_record')
    def test_excludes_records_with_missing_labels(self, mock_fetch):
        """Test that records without degradation labels are excluded."""
        mock_fetch.return_value = {
            "smiles": "CCO",
            "temperature": 25.0,
            # Missing degradation_pathway
        }
        
        with pytest.raises(RuntimeError, match="No real polymer degradation records"):
            download_records_from_nist(material_ids=["test-id"])
    
    @patch('code.ingest._fetch_nist_record')
    def test_excludes_records_with_invalid_smiles(self, mock_fetch):
        """Test that records with invalid SMILES are excluded."""
        mock_fetch.return_value = {
            "smiles": "invalid_smiles",
            "degradation_pathway": "hydrolysis",
            "temperature": 25.0,
            "ph": 7.0,
            "uv_intensity": None,
            "other_conditions": {},
            "metadata": {}
        }
        
        with pytest.raises(RuntimeError, match="No real polymer degradation records"):
            download_records_from_nist(material_ids=["test-id"])

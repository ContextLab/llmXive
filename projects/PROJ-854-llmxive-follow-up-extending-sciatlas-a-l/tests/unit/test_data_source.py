"""
Unit tests to validate data source reachability for the OpenAlex API.

This module verifies that:
1. The OpenAlex API endpoint is reachable via HTTP.
2. The `pyalex` library can successfully fetch a sample record.
3. The fetched data contains expected structural fields.

These tests act as a pre-flight check before running the full ingestion pipeline.
"""
import pytest
import requests
from typing import Dict, Any
import pyalex
from pyalex import Works

# Constants for testing
OPENALEX_API_URL = "https://api.openalex.org"
SAMPLE_WORK_ID = "W2741809807"  # A known, stable OpenAlex work ID (e.g., a classic paper)
REQUEST_TIMEOUT = 10  # Seconds

def test_openalex_api_endpoint_reachable():
    """
    Verify that the OpenAlex API base URL is reachable and returns a 200 OK status.
    """
    try:
        response = requests.get(OPENALEX_API_URL, timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200, f"API returned status {response.status_code}"
    except requests.exceptions.RequestException as e:
        pytest.fail(f"OpenAlex API endpoint is unreachable: {e}")

def test_pyalex_fetch_sample_record():
    """
    Verify that pyalex can fetch a specific, known work from OpenAlex.
    
    This ensures the library is correctly configured and the API is returning
    valid JSON data for a specific resource.
    """
    try:
        # Initialize pyalex (optional, but good practice to ensure connection)
        pyalex.config.email = "researcher@example.com"  # Best practice: identify your bot
        
        # Attempt to fetch the specific work
        work = Works()[SAMPLE_WORK_ID]
        
        assert work is not None, "Failed to fetch work object"
        assert "id" in work, "Fetched work missing 'id' field"
        assert "title" in work, "Fetched work missing 'title' field"
        assert "doi" in work, "Fetched work missing 'doi' field"
        
        # Verify the ID matches the requested one
        assert work["id"].endswith(SAMPLE_WORK_ID), "Returned ID does not match requested ID"
        
    except pyalex.OpenAlexError as e:
        pytest.fail(f"pyalex failed to fetch record: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error during pyalex fetch: {e}")

def test_pyalex_basic_query():
    """
    Verify that pyalex can perform a basic search query (e.g., count of works).
    
    This tests the API's ability to handle query parameters, not just ID lookups.
    """
    try:
        # Query for a very common term to ensure a result exists
        # We use a small sample to keep it fast
        result = Works().filter(openalex="W2741809807").sample(1)
        
        assert len(result) == 1, "Sample query did not return exactly 1 result"
        assert result[0]["id"].endswith(SAMPLE_WORK_ID), "Sampled work ID mismatch"
        
    except Exception as e:
        pytest.fail(f"pyalex basic query failed: {e}")
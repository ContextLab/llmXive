import pytest
import pyalex
from pyalex import Works
from src.lib import config

SAMPLE_WORK_ID = "2741809807"

def test_openalex_reachable():
    """
    Verify that the OpenAlex API is reachable.
    """
    try:
        # Perform a simple count query
        count = Works().filter(openalex="W2741809807").count()
        assert count >= 0, "Count should be non-negative"
    except Exception as e:
        pytest.fail(f"OpenAlex API unreachable: {e}")

def test_pyalex_basic_query():
    """
    Verify that pyalex can perform a basic search query.
    """
    try:
        # Query for a specific work ID using filter
        result = list(Works().filter(openalex=f"W{SAMPLE_WORK_ID}"))
        
        assert len(result) == 1, "Sample query did not return exactly 1 result"
        assert result[0]["id"].endswith(SAMPLE_WORK_ID), "Sampled work ID mismatch"
    except Exception as e:
        pytest.fail(f"pyalex basic query failed: {e}")
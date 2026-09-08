import pytest
import pyalex
from pyalex import Works
from src.lib import config

SAMPLE_WORK_ID = "W2741809807"

def test_openalex_reachable():
    """
    Verify that the OpenAlex API is reachable.
    """
    try:
        # Perform a simple count query
        count = Works().filter(openalex="W2741809807").count()
        assert count >= 0
    except Exception as e:
        pytest.fail(f"OpenAlex API unreachable: {e}")

def test_pyalex_basic_query():
    """
    Verify that pyalex can perform a basic search query (e.g., count of works).
    """
    try:
        # Query for a specific work ID to ensure it exists
        # We use .get() for direct ID lookup which is more reliable than filter().sample()
        work = Works().get(f"https://openalex.org/{SAMPLE_WORK_ID}")
        
        assert work is not None, "Work not found"
        assert work['id'].endswith(SAMPLE_WORK_ID), "Sampled work ID mismatch"
        
    except Exception as e:
        pytest.fail(f"pyalex basic query failed: {e}")

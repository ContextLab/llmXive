import pytest
import pyalex
from pyalex import Works

def test_openalex_reachable():
    """
    Verify the OpenAlex API endpoint is reachable and pyalex can fetch a sample record.
    """
    try:
        # Fetch a single known work or a sample
        # Using a filter to get a specific work if we know an ID, or just sample
        # We'll try to fetch a sample of 1 work
        works = list(Works().sample(1))
        
        assert len(works) == 1
        assert works[0].id is not None
    except Exception as e:
        pytest.fail(f"OpenAlex API is unreachable or failed to fetch sample: {e}")

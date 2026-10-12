"""
Unit tests for the ADS search script (T048.0a).

The tests verify that the helper functions behave correctly given
controlled input.  They deliberately avoid making real network calls –
the public ADS API requires an authentication token and would make the
test suite flaky.  Instead, we mock ``requests.get`` and test the parsing
and filtering logic.

The script itself is executed as an external process in the task
implementation, but the internal helpers are exercised here.
"""

import builtins
import json
import os
import re
from unittest import mock

import pytest

# Import the module under test
from code.research.ads_search import (
    _extract_precision,
    _filter_candidates,
    PRECISION_THRESHOLD,
)

def test_extract_precision_success():
    abstract = (
        "We achieve a precision of 2.5 e -14 in the measurement of the "
        "Eötvös parameter using satellite laser ranging."
    )
    value = _extract_precision(abstract)
    assert pytest.approx(value, rel=1e-12) == 2.5e-14

def test_extract_precision_failure():
    abstract = "This paper does not contain a numeric precision value."
    assert _extract_precision(abstract) is None

def test_filter_candidates_basic():
    # Construct three mock ADS entries
    docs = [
        {
            "title": ["Paper A"],
            "author": ["Doe, J."],
            "abstract": "Precision 1.2 e -13 achieved.",
            "doi": ["10.1234/abcde"],
            "bibcode": "2021XYZ12345",
            "pubdate": "2021-05-01",
        },
        {
            "title": ["Paper B"],
            "author": ["Smith, A."],
            "abstract": "Our result: precision 5 e -14.",
            "doi": ["10.5678/fghij"],
            "bibcode": "2015XYZ67890",
            "pubdate": "2015-03-20",
        },
        {
            "title": ["Paper C"],
            "author": ["Brown, C."],
            "abstract": "No precision mentioned here.",
            "doi": ["10.0000/none"],
            "bibcode": "2022XYZ00000",
            "pubdate": "2022-01-10",
        },
    ]

    candidates = _filter_candidates(docs)

    # Only Paper B meets the < 1e-13 threshold
    assert len(candidates) == 1
    cand = candidates[0]
    assert cand["title"] == "Paper B"
    assert cand["year"] == 2015
    assert pytest.approx(cand["precision"], rel=1e-12) == 5e-14

@mock.patch("code.research.ads_search.requests.get")
def test_fetch_ads_results_mocked(mock_get):
    # Mock the JSON payload returned by the ADS API
    mock_response = mock.Mock()
    mock_response.raise_for_status = mock.Mock()
    mock_response.json.return_value = {
        "response": {
            "docs": [
                {
                    "title": ["Mocked Paper"],
                    "author": ["Tester"],
                    "abstract": "Precision 9.9 e -15 demonstrated.",
                    "doi": ["10.1111/mock"],
                    "bibcode": "2020XYZ11111",
                    "pubdate": "2020-07-15",
                }
            ]
        }
    }
    mock_get.return_value = mock_response

    # Temporarily set the environment variable required for the token
    os.environ["ADS_API_TOKEN"] = "dummy-token"

    # Import the function after setting the env var
    from code.research.ads_search import _fetch_ads_results

    docs = _fetch_ads_results("dummy-token")
    assert isinstance(docs, list)
    assert docs[0]["title"] == ["Mocked Paper"]
    # Clean up
    del os.environ["ADS_API_TOKEN"]
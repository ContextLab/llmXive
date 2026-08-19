"""
Unit tests for code/retrieval.py
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from pathlib import Path

from retrieval import (
    fetch_observed_results,
    _resolve_doi_to_url,
    _parse_data_links_from_files,
    _extract_observed_effect_from_text,
    RetrievalError
)

@pytest.fixture
def mock_study_record():
    return {
        "osf_id": "abc123",
        "planned_power": 0.8,
        "target_n": 50,
        "doi": "10.1234/test_doi",
        "abstract": "We found a significant effect, d = 0.5, with n = 100 participants."
    }

@pytest.fixture
def mock_osf_files():
    return [
        {
            "name": "data.csv",
            "links": {"download": "https://osf.io/download/xyz"}
        },
        {
            "name": "readme.txt",
            "links": {"download": "https://osf.io/download/abc"}
        }
    ]

def test_parse_data_links_from_files(mock_osf_files):
    urls = _parse_data_links_from_files(mock_osf_files)
    assert len(urls) == 1
    assert urls[0] == "https://osf.io/download/xyz"

def test_parse_data_links_from_files_no_data(mock_osf_files):
    # Modify to remove data files
    no_data_files = [
        {
            "name": "readme.txt",
            "links": {"download": "https://osf.io/download/abc"}
        }
    ]
    urls = _parse_data_links_from_files(no_data_files)
    assert len(urls) == 0

def test_extract_observed_effect_from_text():
    text = "The study found a significant effect (d = 0.75) in the treatment group."
    effect = _extract_observed_effect_from_text(text)
    assert effect == 0.75

def test_extract_observed_effect_from_text_no_match():
    text = "The study was conducted with great care."
    effect = _extract_observed_effect_from_text(text)
    assert effect is None

@patch('retrieval.fetch_with_backoff')
def test_resolve_doi_to_url(mock_fetch):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message": {
            "items": [
                {
                    "link": [{"URL": "https://example.com/data.csv"}]
                }
            ]
        }
    }
    mock_fetch.return_value = mock_response
    
    url = _resolve_doi_to_url("10.1234/test")
    assert url == "https://example.com/data.csv"

@patch('retrieval.fetch_with_backoff')
def test_resolve_doi_to_url_not_found(mock_fetch):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_fetch.return_value = mock_response
    
    url = _resolve_doi_to_url("10.1234/invalid")
    assert url is None

@patch('retrieval.get_study_files')
@patch('retrieval._resolve_doi_to_url')
@patch('retrieval._extract_observed_effect_from_text')
def test_fetch_observed_results_success(
    mock_extract_effect,
    mock_resolve_doi,
    mock_get_files,
    mock_study_record,
    mock_osf_files
):
    # Setup mocks
    mock_get_files.return_value = mock_osf_files
    mock_resolve_doi.return_value = None # No DOI needed if files found
    mock_extract_effect.return_value = 0.5
    
    result = fetch_observed_results(mock_study_record)
    
    assert result["osf_id"] == "abc123"
    assert result["observed_effect_size"] == 0.5
    assert result["actual_sample_size"] == 100 # Extracted from abstract
    assert result["missing_data_flag"] is False
    assert "DATA_FOUND" in result["retrieval_notes"]

@patch('retrieval.get_study_files')
@patch('retrieval._resolve_doi_to_url')
def test_fetch_observed_results_missing_data(
    mock_resolve_doi,
    mock_get_files,
    mock_study_record
):
    # Setup mocks to simulate failure
    mock_get_files.return_value = []
    mock_resolve_doi.return_value = None
    
    result = fetch_observed_results(mock_study_record)
    
    assert result["missing_data_flag"] is True
    assert "NO_DATA_FOUND" in result["retrieval_notes"]

def test_fetch_observed_results_missing_osf_id():
    record = {"planned_power": 0.8}
    with pytest.raises(RetrievalError):
        fetch_observed_results(record)

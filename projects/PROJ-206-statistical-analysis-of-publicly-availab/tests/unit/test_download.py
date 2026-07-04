"""
Unit tests for T009a: Data Acquisition.
"""
import sys
import os
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import io

# Add src to path if running from root
if "code" in os.getcwd():
    sys.path.insert(0, os.path.join(os.getcwd(), "src"))
elif os.getcwd().endswith("PROJ-206-statistical-analysis-of-publicly-availab"):
    sys.path.insert(0, os.path.join(os.getcwd(), "src"))

from data.download import fetch_fivethirtyeight_polls, fetch_medsl_outcomes

@patch('data.download.requests.get')
def test_fetch_fivethirtyeight_success(mock_get):
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "date,pollster,vote_share,sample_size\n2023-01-01,ABC,45.5,1000\n2023-01-02,XYZ,46.2,1200"
    mock_get.return_value = mock_response

    df = fetch_fivethirtyeight_polls()

    assert df is not None
    assert len(df) == 2
    assert "date" in df.columns
    assert "vote_share" in df.columns
    mock_get.assert_called_once()

@patch('data.download.requests.get')
def test_fetch_fivethirtyeight_failure(mock_get):
    # Mock request exception
    mock_get.side_effect = Exception("Network error")

    df = fetch_fivethirtyeight_polls()

    assert df is None

@patch('data.download.requests.get')
def test_fetch_medsl_success(mock_get):
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "state,candidate,party,votes,percent\nMA,Joe B,D,123,55\nNY,Joe B,D,456,60"
    mock_get.return_value = mock_response

    df = fetch_medsl_outcomes()

    assert df is not None
    assert len(df) == 2
    assert "state" in df.columns
    assert "percent" in df.columns
    mock_get.assert_called_once()

@patch('data.download.requests.get')
def test_fetch_medsl_failure(mock_get):
    # Mock request exception
    mock_get.side_effect = Exception("Network error")

    df = fetch_medsl_outcomes()

    assert df is None
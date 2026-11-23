import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import json
import pandas as pd
import numpy as np

from src.ingestion.agp_loader import (
    get_project_root,
    verify_url,
    ensure_qiita_token,
    calculate_file_checksum,
    record_checksum,
    fetch_sample_mapping,
    fetch_otu_table,
    fetch_agp_data,
    build_arg_parser,
    main
)

@patch('src.ingestion.agp_loader.get_project_root')
def test_get_project_root(mock_root):
    """Test that get_project_root returns a Path object."""
    mock_root.return_value = Path("/fake/project/root")
    assert get_project_root() == Path("/fake/project/root")

@patch('src.ingestion.agp_loader.requests.head')
def test_verify_url(mock_head):
    """Test URL verification with a 200 response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_head.return_value = mock_response

    assert verify_url("http://example.com") is True

@patch('src.ingestion.agp_loader.requests.head')
def test_verify_url_failure(mock_head):
    """Test URL verification with a 404 response."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status = MagicMock(side_effect=Exception("404"))
    mock_head.return_value = mock_response

    assert verify_url("http://example.com") is False

def test_ensure_qiita_token_missing(monkeypatch):
    """Test that ensure_qiita_token raises RuntimeError if token is missing."""
    monkeypatch.delenv("QIITA_API_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="Qiita API token not found"):
        ensure_qiita_token()

def test_ensure_qiita_token_present(monkeypatch):
    """Test that ensure_qiita_token returns the token."""
    monkeypatch.setenv("QIITA_API_TOKEN", "test_token_123")
    assert ensure_qiita_token() == "test_token_123"

def test_calculate_file_checksum(tmp_path):
    """Test checksum calculation."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")
    
    checksum = calculate_file_checksum(test_file)
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA256 length

@patch('src.ingestion.agp_loader.Path.exists')
@patch('src.ingestion.agp_loader.Path.open')
def test_record_checksum(mock_open, mock_exists, tmp_path):
    """Test recording checksum to state file."""
    # Mock exists to return False first (new file)
    mock_exists.return_value = False
    
    state_file = tmp_path / "state.json"
    record_checksum(tmp_path / "file.txt", "abc123", "test_artifact", state_file)
    
    # Verify file was created
    assert state_file.exists()
    with open(state_file, 'r') as f:
        data = json.load(f)
    assert "test_artifact" in data
    assert data["test_artifact"]["checksum"] == "abc123"

@patch('src.ingestion.agp_loader.requests.get')
def test_fetch_sample_mapping(mock_get, tmp_path):
    """Test fetching sample mapping."""
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "samples": {
            "sample_1": {"fiber_g_day": 25, "age": 30},
            "sample_2": {"fiber_g_day": 10, "age": 45}
        }
    }
    mock_get.return_value = mock_response

    output_path = tmp_path / "samples.tsv"
    df = fetch_sample_mapping("10317", "token", output_path)

    assert len(df) == 2
    assert "sample_id" in df.columns
    assert "fiber_g_day" in df.columns
    assert output_path.exists()

@patch('src.ingestion.agp_loader.requests.get')
def test_fetch_otu_table(mock_get, tmp_path):
    """Test fetching OTU table."""
    # Mock response for a small table
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "otu_1": {"sample_1": 100, "sample_2": 200},
        "otu_2": {"sample_1": 50, "sample_2": 150}
    }
    mock_get.return_value = mock_response

    output_path = tmp_path / "otu.tsv"
    df = fetch_otu_table("10317", "token", output_path)

    assert df.shape == (2, 2)
    assert output_path.exists()

@patch('src.ingestion.agp_loader.fetch_sample_mapping')
@patch('src.ingestion.agp_loader.fetch_otu_table')
@patch('src.ingestion.agp_loader.calculate_file_checksum')
@patch('src.ingestion.agp_loader.record_checksum')
@patch('src.ingestion.agp_loader.get_project_root')
@patch('src.ingestion.agp_loader.ensure_qiita_token')
def test_fetch_agp_data(
    mock_token, mock_root, mock_record, mock_checksum, mock_otu, mock_sample, tmp_path
):
    """Test the main fetch_agp_data function."""
    mock_token.return_value = "fake_token"
    mock_root.return_value = tmp_path / "project"
    (mock_root.return_value / "data").mkdir(parents=True, exist_ok=True)
    (mock_root.return_value / "state").mkdir(parents=True, exist_ok=True)
    
    mock_sample_df = pd.DataFrame({"sample_id": ["s1"], "fiber": [10]})
    mock_sample.return_value = mock_sample_df
    
    mock_otu_df = pd.DataFrame({"otu1": [100], "otu2": [200]})
    mock_otu.return_value = mock_otu_df
    
    mock_checksum.return_value = "fake_checksum"
    
    output_path = tmp_path / "project" / "data" / "raw" / "agp_raw.tsv"
    meta_df, otu_df = fetch_agp_data(output_path)
    
    assert meta_df is not None
    assert otu_df is not None
    assert output_path.exists()

def test_build_arg_parser():
    """Test argument parser construction."""
    parser = build_arg_parser()
    args = parser.parse_args(["--output", "test.tsv"])
    assert args.output == "test.tsv"
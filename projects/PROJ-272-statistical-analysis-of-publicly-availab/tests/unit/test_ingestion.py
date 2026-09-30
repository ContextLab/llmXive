"""
Unit tests for ingestion module.
"""
import pytest
import pandas as pd
from pathlib import Path
import json
import tempfile
import os

from ingestion import (
    clean_transcript_text,
    parse_cognitive_status,
    validate_scope,
    count_raw_records_from_csv,
    DataSourceConfig
)

def test_clean_transcript_text_removes_annotations():
    """Test that non-verbal annotations are removed."""
    text = "Hello <laughter> world <pause>!"
    cleaned = clean_transcript_text(text)
    assert "<laughter>" not in cleaned
    assert "<pause>" not in cleaned
    assert "Hello world !" in cleaned

def test_clean_transcript_text_normalizes_whitespace():
    """Test that whitespace is normalized."""
    text = "Hello   world   !"
    cleaned = clean_transcript_text(text)
    assert "  " not in cleaned
    assert "Hello world !" in cleaned

def test_parse_cognitive_status_control():
    """Test parsing of Control status."""
    header = "ID: P001, Status: Control"
    status = parse_cognitive_status(header)
    assert status == "Control"

def test_parse_cognitive_status_ad():
    """Test parsing of AD status."""
    header = "ID: P002, Status: AD"
    status = parse_cognitive_status(header)
    assert status == "AD"

def test_parse_cognitive_status_mci():
    """Test parsing of MCI status."""
    header = "ID: P003, Status: MCI"
    status = parse_cognitive_status(header)
    assert status == "MCI"

def test_parse_cognitive_status_none():
    """Test parsing when status is not found."""
    header = "ID: P004, Some other info"
    status = parse_cognitive_status(header)
    assert status is None

def test_validate_scope_adress():
    """Test validation for ADReSS source."""
    config = DataSourceConfig(source="ADReSS")
    try:
        validate_scope(config)
    except ValueError:
        pytest.fail("validate_scope raised ValueError for valid ADReSS source")

def test_validate_scope_dementiabank():
    """Test validation fails for DementiaBank source."""
    config = DataSourceConfig(source="DementiaBank")
    with pytest.raises(ValueError, match="DementiaBank is explicitly excluded"):
        validate_scope(config)

def test_validate_scope_missing():
    """Test validation fails for missing source."""
    config = DataSourceConfig(source="")
    with pytest.raises(ValueError, match="Dataset source configuration is missing"):
        validate_scope(config)

def test_count_raw_records_from_csv():
    """Test counting records in a CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("id,label,text\n1,Control,Hello world\n2,AD,Test text\n")
        temp_path = Path(f.name)
    
    try:
        count = count_raw_records_from_csv(temp_path)
        assert count == 2
    finally:
        os.unlink(temp_path)

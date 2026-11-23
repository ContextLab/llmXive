"""
Test for T008b: Verify Research Sources
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
from ingestion.run_reference_validation import (
    load_candidate_sources,
    verify_source,
    run_verification,
    SourceVerificationError
)

def test_verify_source_valid():
    """Test verification of a valid source."""
    source = {
        "url": "https://materialsproject.org/rest/v2/materials/",
        "source_type": "api",
        "citation": "Materials Project API Documentation"
    }
    is_valid, reason = verify_source(source)
    assert is_valid is True
    assert reason == "Verified"

def test_verify_source_missing_url():
    """Test verification fails for missing URL."""
    source = {
        "url": "",
        "source_type": "api",
        "citation": "Test citation"
    }
    is_valid, reason = verify_source(source)
    assert is_valid is False
    assert "Missing URL" in reason

def test_verify_source_missing_citation():
    """Test verification fails for missing citation."""
    source = {
        "url": "https://example.com",
        "source_type": "api",
        "citation": ""
    }
    is_valid, reason = verify_source(source)
    assert is_valid is False
    assert "Missing citation" in reason

def test_verify_source_invalid_url():
    """Test verification fails for invalid URL format."""
    source = {
        "url": "not-a-url",
        "source_type": "api",
        "citation": "Test citation"
    }
    is_valid, reason = verify_source(source)
    assert is_valid is False
    assert "Invalid URL format" in reason

def test_verify_source_placeholder():
    """Test verification fails for placeholder URL."""
    source = {
        "url": "https://example.com",
        "source_type": "api",
        "citation": "Test citation"
    }
    # Modify URL to contain placeholder
    source["url"] = "https://placeholder.example.com"
    is_valid, reason = verify_source(source)
    assert is_valid is False
    assert "Placeholder URL detected" in reason

def test_run_verification_empty_list():
    """Test verification fails for empty source list."""
    with pytest.raises(SourceVerificationError):
        run_verification([])

def test_run_verification_all_valid():
    """Test verification succeeds when all sources are valid."""
    sources = [
        {
            "url": "https://materialsproject.org/rest/v2/materials/",
            "source_type": "api",
            "citation": "Materials Project API Documentation"
        },
        {
            "url": "https://arxiv.org/search/?query=solder+hardness&searchtype=all",
            "source_type": "html",
            "citation": "ArXiv Search for Solder Hardness"
        }
    ]
    verified = run_verification(sources)
    assert len(verified) == 2

def test_run_verification_one_invalid():
    """Test verification fails when one source is invalid."""
    sources = [
        {
            "url": "https://materialsproject.org/rest/v2/materials/",
            "source_type": "api",
            "citation": "Materials Project API Documentation"
        },
        {
            "url": "",
            "source_type": "api",
            "citation": "Invalid Source"
        }
    ]
    with pytest.raises(SourceVerificationError):
        run_verification(sources)

def test_load_candidate_sources_missing_file():
    """Test loading candidate sources fails for missing file."""
    with pytest.raises(FileNotFoundError):
        load_candidate_sources(Path("nonexistent.json"))

def test_load_candidate_sources_invalid_json():
    """Test loading candidate sources fails for invalid JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("invalid json")
        temp_path = f.name
    
    try:
        with pytest.raises(json.JSONDecodeError):
            load_candidate_sources(Path(temp_path))
    finally:
        os.unlink(temp_path)

def test_load_candidate_sources_not_list():
    """Test loading candidate sources fails if not a list."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"key": "value"}, f)
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError):
            load_candidate_sources(Path(temp_path))
    finally:
        os.unlink(temp_path)

def test_load_candidate_sources_valid():
    """Test loading candidate sources succeeds for valid input."""
    sources = [
        {
            "url": "https://materialsproject.org/rest/v2/materials/",
            "source_type": "api",
            "citation": "Materials Project API Documentation"
        }
    ]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sources, f)
        temp_path = f.name
    
    try:
        loaded = load_candidate_sources(Path(temp_path))
        assert len(loaded) == 1
        assert loaded[0]["url"] == sources[0]["url"]
    finally:
        os.unlink(temp_path)

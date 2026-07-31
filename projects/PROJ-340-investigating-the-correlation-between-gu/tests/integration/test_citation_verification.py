"""
Integration tests for T085: Citation Verification.

Tests the verification logic against real and fake citations.
"""
import pytest
import os
import sys
import tempfile
import json
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from verify_citation import (
    load_verified_dois,
    extract_citation_from_file,
    verify_citation,
    run_citation_verification,
    CitationVerificationError
)

@pytest.fixture
def verified_dois_file(tmp_path):
    """Create a temporary verified_dois.yaml file."""
    content = """
verified_dois:
  - "10.5281/zenodo.1234567"
  - "10.1038/s41591-023-02345-x"
"""
    file_path = tmp_path / "verified_dois.yaml"
    file_path.write_text(content)
    return str(file_path)

@pytest.fixture
def valid_data_file(tmp_path):
    """Create a temporary CSV with a valid DOI."""
    content = """subject_id,Bacteroides,doi
S001,1250,10.5281/zenodo.1234567
S002,1180,10.5281/zenodo.1234567
"""
    file_path = tmp_path / "valid_data.csv"
    file_path.write_text(content)
    return str(file_path)

@pytest.fixture
def invalid_data_file(tmp_path):
    """Create a temporary CSV with an invalid DOI."""
    content = """subject_id,Bacteroides,doi
S001,1250,10.9999/fake.doi
"""
    file_path = tmp_path / "invalid_data.csv"
    file_path.write_text(content)
    return str(file_path)

@pytest.fixture
def missing_doi_file(tmp_path):
    """Create a temporary CSV with no DOI column."""
    content = """subject_id,Bacteroides,count
S001,1250,500
"""
    file_path = tmp_path / "missing_doi.csv"
    file_path.write_text(content)
    return str(file_path)

def test_load_verified_dois(verified_dois_file):
    """Test loading the verified DOIs list."""
    dois = load_verified_dois(verified_dois_file)
    assert "10.5281/zenodo.1234567" in dois
    assert "10.1038/s41591-023-02345-x" in dois
    assert len(dois) == 2

def test_extract_citation_from_file_valid(valid_data_file):
    """Test extracting DOI from a valid CSV."""
    doi = extract_citation_from_file(valid_data_file)
    assert doi == "10.5281/zenodo.1234567"

def test_extract_citation_from_file_missing(missing_doi_file):
    """Test extraction returns None when DOI is missing."""
    doi = extract_citation_from_file(missing_doi_file)
    assert doi is None

def test_verify_citation_valid(valid_data_file, verified_dois_file):
    """Test verification passes for a valid DOI."""
    dois = load_verified_dois(verified_dois_file)
    extracted = extract_citation_from_file(valid_data_file)
    assert verify_citation(extracted, dois) is True

def test_verify_citation_invalid(invalid_data_file, verified_dois_file):
    """Test verification fails for an invalid DOI."""
    dois = load_verified_dois(verified_dois_file)
    extracted = extract_citation_from_file(invalid_data_file)
    with pytest.raises(CitationVerificationError):
        verify_citation(extracted, dois)

def test_verify_citation_missing(missing_doi_file, verified_dois_file):
    """Test verification fails when DOI is missing."""
    dois = load_verified_dois(verified_dois_file)
    extracted = extract_citation_from_file(missing_doi_file)
    with pytest.raises(CitationVerificationError):
        verify_citation(extracted, dois)

def test_run_citation_verification_success(valid_data_file, verified_dois_file):
    """Test the full pipeline with valid data."""
    result = run_citation_verification(valid_data_file, verified_dois_file)
    assert result["status"] == "VERIFIED"
    assert result["verified"] is True

def test_run_citation_verification_failure(invalid_data_file, verified_dois_file):
    """Test the full pipeline with invalid data."""
    with pytest.raises(CitationVerificationError):
        run_citation_verification(invalid_data_file, verified_dois_file)
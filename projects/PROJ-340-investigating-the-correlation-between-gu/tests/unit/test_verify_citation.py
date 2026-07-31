"""
Unit tests for T085: Citation Verification.
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
import yaml

# Import the module under test
from code.verify_citation import (
    run_citation_verification,
    CitationVerificationError,
    load_verified_dois,
    extract_citation_from_file,
    verify_citation
)

@pytest.fixture
def temp_verified_dois_file():
    """Creates a temporary verified_dois.yaml file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({
            "verified_dois": [
                "10.1234/test.doi.1",
                "https://doi.org/10.5678/test.doi.2"
            ]
        }, f)
        path = f.name
    yield path
    os.unlink(path)

@pytest.fixture
def temp_data_file_with_doi():
    """Creates a temporary CSV file with a DOI in comments."""
    content = """# Source: Gut Microbiome Study
    # DOI: 10.1234/test.doi.1
    subject_id,taxon_a,sleep_duration
    1,100,7.5
    2,120,8.0
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(content)
        path = f.name
    yield path
    os.unlink(path)

@pytest.fixture
def temp_data_file_no_doi():
    """Creates a temporary CSV file without a DOI."""
    content = """subject_id,taxon_a,sleep_duration
    1,100,7.5
    2,120,8.0
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(content)
        path = f.name
    yield path
    os.unlink(path)

def test_load_verified_dois_success(temp_verified_dois_file):
    dois = load_verified_dois(temp_verified_dois_file)
    assert len(dois) == 2
    assert "10.1234/test.doi.1" in dois

def test_extract_citation_from_file(temp_data_file_with_doi):
    doi = extract_citation_from_file(temp_data_file_with_doi)
    assert doi == "10.1234/test.doi.1"

def test_extract_citation_from_file_no_doi(temp_data_file_no_doi):
    doi = extract_citation_from_file(temp_data_file_no_doi)
    assert doi is None

def test_verify_citation_success(temp_verified_dois_file):
    dois = load_verified_dois(temp_verified_dois_file)
    assert verify_citation("10.1234/test.doi.1", dois) is True
    assert verify_citation("https://doi.org/10.5678/test.doi.2", dois) is True

def test_verify_citation_failure(temp_verified_dois_file):
    dois = load_verified_dois(temp_verified_dois_file)
    assert verify_citation("10.9999/fake.doi", dois) is False

def test_run_citation_verification_success(temp_verified_dois_file, temp_data_file_with_doi):
    result = run_citation_verification(temp_data_file_with_doi, temp_verified_dois_file)
    assert result["status"] == "VERIFIED"
    assert result["citation"] == "10.1234/test.doi.1"

def test_run_citation_verification_missing_citation(temp_verified_dois_file, temp_data_file_no_doi):
    with pytest.raises(CitationVerificationError) as exc_info:
        run_citation_verification(temp_data_file_no_doi, temp_verified_dois_file)
    assert "No valid DOI" in str(exc_info.value)

def test_run_citation_verification_invalid_citation(temp_verified_dois_file, temp_data_file_with_doi):
    # Create a file with a DOI that is NOT in the verified list
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("# DOI: 10.9999/fake.doi\n")
        f.write("id,val\n1,1\n")
        bad_path = f.name
    
    try:
        with pytest.raises(CitationVerificationError) as exc_info:
            run_citation_verification(bad_path, temp_verified_dois_file)
        assert "not in the list of verified DOIs" in str(exc_info.value)
    finally:
        os.unlink(bad_path)

import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from discovery.query_geno import (
    tokenize_title,
    calculate_token_overlap,
    validate_reference,
    search_geo,
    search_encode,
    filter_by_organism,
    check_metadata_completeness,
    run_discovery,
    load_verified_datasets
)

@pytest.fixture
def mock_verified_datasets(tmp_path):
    """Create a temporary verified_datasets.yaml file."""
    data = {
        "verified_datasets": [
            {
                "accession": "GSE12345",
                "title": "Multi-generational methylation and RNA-seq in mouse under fluctuating temperature",
                "source": "GEO"
            },
            {
                "accession": "ENCODE123",
                "title": "Fluctuating nutrient levels affect gene expression in C. elegans",
                "source": "ENCODE"
            }
        ],
        "last_updated": "2026-06-27"
    }
    file_path = tmp_path / "verified_datasets.yaml"
    import yaml
    with open(file_path, 'w') as f:
        yaml.dump(data, f)
    return file_path

def test_tokenize_title():
    assert tokenize_title("Hello World!") == ["hello", "world"]
    assert tokenize_title("") == []
    assert tokenize_title("Multi-generational") == ["multi", "generational"]

def test_calculate_token_overlap():
    t1 = ["a", "b", "c"]
    t2 = ["b", "c", "d"]
    # Intersection: 2 (b, c), Union: 4 (a, b, c, d) -> 0.5
    assert calculate_token_overlap(t1, t2) == 0.5
    assert calculate_token_overlap([], ["a"]) == 0.0
    assert calculate_token_overlap(["a"], []) == 0.0

def test_validate_reference_no_verified(mock_verified_datasets):
    # Temporarily override the path for testing
    import discovery.query_geno as qg
    original_load = qg.load_verified_datasets
    
    def mock_load():
        return [
            {"title": "Test Dataset A"},
            {"title": "Test Dataset B"}
        ]
    
    qg.load_verified_datasets = mock_load
    try:
        # Should fail if no overlap
        assert not validate_reference("GSE000", "Completely Different Title")
        # Should pass if overlap
        assert validate_reference("GSE001", "Test Dataset A")
    finally:
        qg.load_verified_datasets = original_load

@patch('discovery.query_geno.requests.get')
def test_search_geo(mock_get):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "ids": ["GSE123", "GSE456"],
        "result": {
            "GSE123": {"id": "GSE123", "title": "Multi-generational methylation RNA-seq mouse"},
            "GSE456": {"id": "GSE456", "title": "Random unrelated study"}
        }
    }
    mock_get.return_value = mock_response
    
    results = search_geo(["multi-generational", "methylation"])
    assert len(results) == 1
    assert results[0]['accession'] == 'GSE123'
    assert results[0]['source'] == 'GEO'

@patch('discovery.query_geno.requests.get')
def test_search_encode(mock_get):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "@graph": [
            {
                "accession": "ENCODE001",
                "description": "Fluctuating environment C. elegans RNA-seq",
                "title": "Fluctuating environment C. elegans RNA-seq"
            },
            {
                "accession": "ENCODE002",
                "description": "Stable environment",
                "title": "Stable environment"
            }
        ]
    }
    mock_get.return_value = mock_response
    
    results = search_encode(["fluctuating", "RNA-seq"])
    assert len(results) == 1
    assert results[0]['accession'] == 'ENCODE001'

def test_filter_by_organism():
    data = [
        {"title": "Mouse study", "accession": "GSE1"},
        {"title": "Fly study", "accession": "GSE2"},
        {"title": "Human study", "accession": "GSE3"}
    ]
    filtered = filter_by_organism(data, ["mouse", "fly"])
    assert len(filtered) == 2
    assert filtered[0]['accession'] == 'GSE1'
    assert filtered[1]['accession'] == 'GSE2'

def test_check_metadata_completeness():
    assert check_metadata_completeness({"accession": "A", "title": "T"}) is True
    assert check_metadata_completeness({"accession": "A"}) is False
    assert check_metadata_completeness({}) is False

@patch('discovery.query_geno.search_geo')
@patch('discovery.query_geno.search_encode')
@patch('discovery.query_geno.load_verified_datasets')
def test_run_discovery(mock_load_ver, mock_search_enc, mock_search_geo, tmp_path):
    # Mock verified datasets
    mock_load_ver.return_value = [
        {"title": "Multi-generational methylation RNA-seq mouse"}
    ]
    
    # Mock search results
    mock_search_geo.return_value = [
        {"accession": "GSE1", "title": "Multi-generational methylation RNA-seq mouse", "source": "GEO"}
    ]
    mock_search_enc.return_value = []
    
    output_file = tmp_path / "test_discovery.json"
    result = run_discovery(str(output_file))
    
    assert result['count'] == 1
    assert result['total_candidates'] == 1
    assert output_file.exists()
    
    with open(output_file) as f:
        data = json.load(f)
        assert 'valid_datasets' in data
        assert len(data['valid_datasets']) == 1
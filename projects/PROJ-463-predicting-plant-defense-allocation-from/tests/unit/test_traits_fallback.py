"""
Unit tests for T025b: Trait fallback data acquisition.
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.traits_fallback import (
    load_fallback_input,
    fetch_traits_from_phenoscape,
    fetch_traits_from_gbif,
    fetch_traits_for_species,
    save_trait_fallback_summary,
    main
)


@pytest.fixture
def temp_species_file(tmp_path):
    """Create a temporary post_qc_species_list.json file."""
    species_data = {
        "species": [
            {"name": "Arabidopsis thaliana", "exclusion_reason": None},
            {"name": "Solanum lycopersicum", "exclusion_reason": None},
            {"name": "Zea mays", "exclusion_reason": None}
        ]
    }
    file_path = tmp_path / "post_qc_species_list.json"
    with open(file_path, 'w') as f:
        json.dump(species_data, f)
    return file_path


@pytest.fixture
def temp_fallback_summary(tmp_path):
    """Create a temporary trait_fallback_summary.json file."""
    summary_data = {
        "target_species": ["Arabidopsis thaliana", "Solanum lycopersicum"],
        "primary_source_results": {
            "Arabidopsis thaliana": {"traits": [{"name": "trichome_density", "value": 10}]}
        },
        "missing_from_try": ["Solanum lycopersicum", "Zea mays"],
        "fallback_results": {},
        "missing_from_all_sources": []
    }
    file_path = tmp_path / "trait_fallback_summary.json"
    with open(file_path, 'w') as f:
        json.dump(summary_data, f)
    return file_path


def test_load_fallback_input_valid(temp_species_file, tmp_path, monkeypatch):
    """Test loading valid fallback input files."""
    # Create a mock fallback summary
    summary_path = tmp_path / "trait_fallback_summary.json"
    summary_data = {
        "missing_from_try": ["Species A", "Species B"]
    }
    with open(summary_path, 'w') as f:
        json.dump(summary_data, f)

    # Monkeypatch the paths
    monkeypatch.setattr('src.data.traits_fallback.POST_QC_SPECIES_PATH', temp_species_file)
    monkeypatch.setattr('src.data.traits_fallback.FALLBACK_SUMMARY_PATH', summary_path)

    result = load_fallback_input()

    assert 'target_species' in result
    assert 'missing_from_try' in result
    assert len(result['target_species']) == 3
    assert result['missing_from_try'] == ["Species A", "Species B"]


@patch('src.data.traits_fallback.requests.get')
def test_fetch_traits_from_phenoscape_mocked(mock_get, temp_species_file, monkeypatch):
    """Test Phenoscape trait fetching with mocked API response."""
    # Mock taxon search response
    mock_taxon_response = MagicMock()
    mock_taxon_response.status_code = 200
    mock_taxon_response.json.return_value = {
        "results": [{"id": "ENT:12345"}]
    }

    # Mock phenotype response
    mock_phenotype_response = MagicMock()
    mock_phenotype_response.status_code = 200
    mock_phenotype_response.json.return_value = {
        "phenotypes": [
            {
                "label": "Trichome density",
                "value": "high",
                "term": {"id": "TO:0000123"}
            },
            {
                "label": "Leaf thickness",
                "value": "0.5mm"
            }
        ]
    }

    # Configure mock to return different responses
    mock_get.side_effect = [mock_taxon_response, mock_phenotype_response]

    # Monkeypatch the path
    monkeypatch.setattr('src.data.traits_fallback.POST_QC_SPECIES_PATH', temp_species_file)

    result = fetch_traits_from_phenoscape("Arabidopsis thaliana")

    assert result is not None
    assert result['species'] == "Arabidopsis thaliana"
    assert result['source'] == 'phenoscape'
    assert len(result['traits']) >= 1  # At least the trichome trait
    assert any('trichome' in t['trait_name'].lower() for t in result['traits'])


@patch('src.data.traits_fallback.requests.get')
def test_fetch_traits_from_gbif_mocked(mock_get, temp_species_file, monkeypatch):
    """Test GBIF trait fetching with mocked API response."""
    # Mock occurrence response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "key": "occurrence123",
                "scientificName": "Arabidopsis thaliana",
                "extensions": {
                    "http://rs.gbif.org/terms/1.0/MeasurementOrFact": {
                        "values": [
                            {
                                "type": "Defense trait",
                                "value": "present",
                                "unit": "binary"
                            }
                        ]
                    }
                }
            }
        ]
    }
    mock_get.return_value = mock_response

    # Monkeypatch the path
    monkeypatch.setattr('src.data.traits_fallback.POST_QC_SPECIES_PATH', temp_species_file)

    result = fetch_traits_from_gbif("Arabidopsis thaliana")

    assert result is not None
    assert result['species'] == "Arabidopsis thaliana"
    assert result['source'] == 'gbif'
    assert len(result['traits']) >= 1


def test_fetch_traits_for_species_integration(temp_species_file, monkeypatch):
    """Test the combined fallback fetch (Phenoscape -> GBIF)."""
    # Monkeypatch to use temp file
    monkeypatch.setattr('src.data.traits_fallback.POST_QC_SPECIES_PATH', temp_species_file)

    # Mock both APIs to return None (no traits found)
    with patch('src.data.traits_fallback.fetch_traits_from_phenoscape', return_value=None), \
         patch('src.data.traits_fallback.fetch_traits_from_gbif', return_value=None):

        result = fetch_traits_for_species("Unknown Species")
        assert result is None


def test_save_trait_fallback_summary(tmp_path, monkeypatch):
    """Test saving the trait fallback summary."""
    summary_data = {
        "target_species": ["Species A"],
        "fallback_results": {"Species A": {"traits": []}},
        "missing_from_try": [],
        "missing_from_all_sources": []
    }

    output_path = tmp_path / "trait_fallback_summary.json"
    monkeypatch.setattr('src.data.traits_fallback.FALLBACK_SUMMARY_PATH', output_path)

    save_trait_fallback_summary(summary_data)

    assert output_path.exists()
    with open(output_path, 'r') as f:
        loaded = json.load(f)
    assert loaded == summary_data


@patch('src.data.traits_fallback.fetch_traits_for_species')
@patch('src.data.traits_fallback.load_fallback_input')
@patch('src.data.traits_fallback.save_trait_fallback_summary')
def test_main(mock_save, mock_load, mock_fetch, temp_species_file, tmp_path, monkeypatch):
    """Test the main function of T025b."""
    # Setup mocks
    mock_load.return_value = {
        'target_species': ['Species A', 'Species B'],
        'missing_from_try': ['Species A']
    }
    mock_fetch.return_value = {
        'species': 'Species A',
        'traits': [{'name': 'test', 'value': 1}],
        'source': 'phenoscape'
    }

    # Monkeypatch paths
    monkeypatch.setattr('src.data.traits_fallback.POST_QC_SPECIES_PATH', temp_species_file)
    summary_path = tmp_path / "trait_fallback_summary.json"
    monkeypatch.setattr('src.data.traits_fallback.FALLBACK_SUMMARY_PATH', summary_path)

    result = main()

    assert result == 0
    mock_save.assert_called_once()
import pytest
import json
import os
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from research.verify_studies import (
    search_studies,
    get_study_metadata,
    check_pre_challenge_profiles,
    check_disease_resistance_metadata,
    verify_studies,
    DataUnavailableError
)

class TestVerifyStudies:
    
    def test_check_pre_challenge_profiles_positive(self):
        """Test detection of pre-challenge profiles."""
        metadata = {
            "DESIGN": "Baseline samples taken before pathogen inoculation",
            "STUDY_TITLE": "Plant Disease Resistance",
            "ABSTRACT": "Analysis of metabolites before infection"
        }
        assert check_pre_challenge_profiles(metadata) is True

    def test_check_pre_challenge_profiles_negative(self):
        """Test rejection of studies without pre-challenge data."""
        metadata = {
            "DESIGN": "Post-infection analysis only",
            "STUDY_TITLE": "Recovery Study",
            "ABSTRACT": "Metabolites after disease onset"
        }
        assert check_pre_challenge_profiles(metadata) is False

    def test_check_disease_resistance_positive(self):
        """Test detection of disease resistance metadata."""
        metadata = {
            "DESIGN": "Comparison of resistant and susceptible lines",
            "STUDY_TITLE": "Fungal Resistance in Wheat",
            "ORGANISM": "Triticum aestivum"
        }
        assert check_disease_resistance_metadata(metadata) is True

    def test_check_disease_resistance_negative(self):
        """Test rejection of studies without disease metadata."""
        metadata = {
            "DESIGN": "General metabolite profiling",
            "STUDY_TITLE": "Plant Growth Study",
            "ABSTRACT": "Effect of fertilizer on growth"
        }
        assert check_disease_resistance_metadata(metadata) is False

    @patch('research.verify_studies.requests.get')
    def test_search_studies_success(self, mock_get):
        """Test successful API search."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "STUDY": [
                {"STUDY_ID": "C-STUDY-001", "TITLE": "Test"},
                {"STUDY_ID": "C-STUDY-002", "TITLE": "Test 2"}
            ]
        }
        mock_get.return_value = mock_response

        results = search_studies(["plant", "disease"])
        assert len(results) == 2
        assert results[0]["STUDY_ID"] == "C-STUDY-001"

    @patch('research.verify_studies.requests.get')
    def test_search_studies_no_results(self, mock_get):
        """Test API search with no results."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"MESSAGE": "No studies found"}
        mock_get.return_value = mock_response

        results = search_studies(["plant", "disease"])
        assert results == []

    @patch('research.verify_studies.requests.get')
    def test_verify_studies_success(self, mock_get):
        """Test verification of valid studies."""
        # Mock search result
        mock_response_search = MagicMock()
        mock_response_search.raise_for_status.return_value = None
        mock_response_search.json.return_value = {
            "STUDY": [
                {"STUDY_ID": "C-STUDY-001"},
                {"STUDY_ID": "C-STUDY-002"}
            ]
        }

        # Mock metadata for study 1 (valid)
        mock_response_meta_1 = MagicMock()
        mock_response_meta_1.raise_for_status.return_value = None
        mock_response_meta_1.json.return_value = {
            "STUDY_ID": "C-STUDY-001",
            "DESIGN": "Baseline before infection",
            "STUDY_TITLE": "Disease Resistance",
            "ABSTRACT": "Plant disease study"
        }

        # Mock metadata for study 2 (valid)
        mock_response_meta_2 = MagicMock()
        mock_response_meta_2.raise_for_status.return_value = None
        mock_response_meta_2.json.return_value = {
            "STUDY_ID": "C-STUDY-002",
            "DESIGN": "Pre-challenge baseline",
            "STUDY_TITLE": "Resistance Study",
            "ABSTRACT": "Pathogen resistance"
        }

        # Side effect: first call is search, next are metadata
        mock_get.side_effect = [
            mock_response_search,
            mock_response_meta_1,
            mock_response_meta_2
        ]

        valid = verify_studies(["C-STUDY-001", "C-STUDY-002"])
        assert len(valid) == 2

    @patch('research.verify_studies.requests.get')
    def test_verify_studies_insufficient(self, mock_get):
        """Test verification when not enough valid studies are found."""
        mock_response_search = MagicMock()
        mock_response_search.raise_for_status.return_value = None
        mock_response_search.json.return_value = {
            "STUDY": [
                {"STUDY_ID": "C-STUDY-001"}
            ]
        }

        mock_response_meta = MagicMock()
        mock_response_meta.raise_for_status.return_value = None
        mock_response_meta.json.return_value = {
            "STUDY_ID": "C-STUDY-001",
            "DESIGN": "Post infection only", # Invalid
            "STUDY_TITLE": "Recovery",
            "ABSTRACT": "No resistance data"
        }

        mock_get.side_effect = [mock_response_search, mock_response_meta]

        with pytest.raises(DataUnavailableError):
            verify_studies(["C-STUDY-001"])
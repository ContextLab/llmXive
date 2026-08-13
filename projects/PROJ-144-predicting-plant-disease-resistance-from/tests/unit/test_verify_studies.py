"""
Unit tests for code/research/verify_studies.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.research.verify_studies import (
    search_studies,
    get_study_metadata,
    check_pre_challenge_profiles,
    check_disease_resistance_metadata,
    verify_studies,
    DataUnavailableError
)


class TestSearchStudies:
    def test_search_studies_success(self):
        """Test successful search returns list of studies."""
        mock_response_data = {
            "STUDY": [
                {"STUDY_ID": "ST001234", "STUDY_TITLE": "Plant Disease Metabolomics", "STUDY_DESCRIPTION": "Study of plant disease", "PROJECT_ID": "P001"}
            ]
        }

        with patch('code.research.verify_studies.requests.get') as mock_get:
            mock_get.return_value = MagicMock()
            mock_get.return_value.raise_for_status = MagicMock()
            mock_get.return_value.json.return_value = mock_response_data

            studies = search_studies(["plant disease", "metabolomics"])

            assert len(studies) == 1
            assert studies[0]["study_id"] == "ST001234"
            mock_get.assert_called_once()

    def test_search_studies_api_error(self):
        """Test that API errors raise DataUnavailableError."""
        with patch('code.research.verify_studies.requests.get') as mock_get:
            mock_get.side_effect = Exception("Connection Error")

            with pytest.raises(DataUnavailableError):
                search_studies(["plant disease"])

    def test_search_studies_no_results(self):
        """Test handling of empty results."""
        mock_response_data = {"STUDY": []}

        with patch('code.research.verify_studies.requests.get') as mock_get:
            mock_get.return_value = MagicMock()
            mock_get.return_value.raise_for_status = MagicMock()
            mock_get.return_value.json.return_value = mock_response_data

            studies = search_studies(["nonexistent term"])
            assert len(studies) == 0


class TestCheckMetadata:
    def test_check_pre_challenge_positive(self):
        """Test detection of temporal keywords."""
        metadata = {
            "STUDY_TITLE": "Time Course of Plant Disease",
            "STUDY_DESCRIPTION": "Samples collected at baseline and post-challenge."
        }
        assert check_pre_challenge_profiles(metadata) is True

    def test_check_pre_challenge_negative(self):
        """Test rejection when no temporal keywords."""
        metadata = {
            "STUDY_TITLE": "General Metabolomics",
            "STUDY_DESCRIPTION": "Study of plant metabolites."
        }
        assert check_pre_challenge_profiles(metadata) is False

    def test_check_disease_resistance_positive(self):
        """Test detection of disease keywords."""
        metadata = {
            "STUDY_TITLE": "Fungal Resistance in Wheat",
            "STUDY_DESCRIPTION": "Analysis of resistance phenotypes."
        }
        assert check_disease_resistance_metadata(metadata) is True

    def test_check_disease_resistance_negative(self):
        """Test rejection when no disease keywords."""
        metadata = {
            "STUDY_TITLE": "Nutrient Analysis",
            "STUDY_DESCRIPTION": "Study of nitrogen content."
        }
        assert check_disease_resistance_metadata(metadata) is False


class TestVerifyStudies:
    def test_verify_studies_filtering(self):
        """Test that verify_studies filters out invalid studies."""
        raw_studies = [
            {
                "study_id": "ST001",
                "title": "Good Study",
                "description": "Baseline and disease data",
                "project_id": "P1"
            },
            {
                "study_id": "ST002",
                "title": "Bad Study",
                "description": "No temporal data",
                "project_id": "P2"
            }
        ]

        # Mock get_study_metadata to return different data for each ID
        def mock_get_metadata(study_id):
            if study_id == "ST001":
                return {
                    "STUDY_TITLE": "Good Study",
                    "STUDY_DESCRIPTION": "Baseline and disease data"
                }
            return {
                "STUDY_TITLE": "Bad Study",
                "STUDY_DESCRIPTION": "No temporal data"
            }

        with patch('code.research.verify_studies.get_study_metadata', side_effect=mock_get_metadata):
            verified = verify_studies(raw_studies)

        assert len(verified) == 1
        assert verified[0]["study_id"] == "ST001"
        assert verified[0]["verified"] is True
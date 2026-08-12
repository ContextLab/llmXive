"""
Unit tests for code/research/verify_studies.py

Tests verify the logic of study verification without making actual API calls.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import json

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.research.verify_studies import (
    check_pre_challenge_profiles,
    check_disease_resistance_metadata,
    verify_studies,
    search_studies
)

class TestPreChallengeDetection:
    """Test pre-challenge profile detection logic."""
    
    def test_baseline_keyword_in_title(self):
        """Detect pre-challenge from 'baseline' in title."""
        metadata = {
            "study_title": "Baseline metabolomics in plant disease resistance",
            "study_abstract": "Study of metabolite changes before infection."
        }
        assert check_pre_challenge_profiles(metadata) is True
    
    def test_control_keyword_in_abstract(self):
        """Detect pre-challenge from 'control' in abstract."""
        metadata = {
            "study_title": "Plant metabolomics",
            "study_abstract": "Comparing control and infected samples."
        }
        assert check_pre_challenge_profiles(metadata) is True
    
    def test_no_pre_challenge_keywords(self):
        """Return False when no pre-challenge keywords present."""
        metadata = {
            "study_title": "General plant metabolomics",
            "study_abstract": "Analysis of plant metabolites."
        }
        assert check_pre_challenge_profiles(metadata) is False
    
    def test_sample_metadata_baseline(self):
        """Detect from sample metadata."""
        metadata = {
            "study_title": "Plant study",
            "samples": [
                {"sample_type": "baseline", "time_point": "0"}
            ]
        }
        assert check_pre_challenge_profiles(metadata) is True
    
    def test_sample_metadata_healthy(self):
        """Detect from healthy sample type."""
        metadata = {
            "study_title": "Plant study",
            "samples": [
                {"sample_type": "healthy control"}
            ]
        }
        assert check_pre_challenge_profiles(metadata) is True

class TestResistanceMetadataDetection:
    """Test disease-resistance metadata detection logic."""
    
    def test_resistance_in_title(self):
        """Detect resistance from title."""
        metadata = {
            "study_title": "Plant disease resistance mechanisms",
            "study_abstract": "Investigating resistance to pathogens."
        }
        assert check_disease_resistance_metadata(metadata) is True
    
    def test_pathogen_in_abstract(self):
        """Detect resistance from pathogen mention."""
        metadata = {
            "study_title": "Metabolomics study",
            "study_abstract": "Response to pathogen infection."
        }
        assert check_disease_resistance_metadata(metadata) is True
    
    def test_no_resistance_keywords(self):
        """Return False when no resistance keywords present."""
        metadata = {
            "study_title": "Plant growth metabolomics",
            "study_abstract": "Study of growth-related metabolites."
        }
        assert check_disease_resistance_metadata(metadata) is False
    
    def test_phenotype_resistance(self):
        """Detect from phenotype metadata."""
        metadata = {
            "study_title": "Plant study",
            "phenotypes": [
                {
                    "phenotype_name": "Disease Resistance Score",
                    "phenotype_description": "Measured resistance levels"
                }
            ]
        }
        assert check_disease_resistance_metadata(metadata) is True
    
    def test_susceptible_keyword(self):
        """Detect from susceptible keyword."""
        metadata = {
            "study_title": "Susceptible and resistant plant varieties",
            "study_abstract": "Comparing plant responses."
        }
        assert check_disease_resistance_metadata(metadata) is True

class TestVerifyStudiesIntegration:
    """Integration tests for the verification workflow."""
    
    @patch('code.research.verify_studies.search_studies')
    @patch('code.research.verify_studies.get_study_metadata')
    def test_finds_verified_studies(self, mock_get_meta, mock_search):
        """Test successful verification of studies."""
        # Mock search results
        mock_search.return_value = [
            {"study_id": "ST001234"},
            {"study_id": "ST005678"}
        ]
        
        # Mock metadata for first study (verified)
        mock_get_meta.side_effect = [
            {
                "study_title": "Plant disease resistance baseline study",
                "study_abstract": "Pre-challenge metabolomics of resistant plants",
                "samples": [{"sample_type": "baseline"}],
                "phenotypes": [{"phenotype_name": "Resistance Score"}]
            },
            {
                "study_title": "General plant study",
                "study_abstract": "No resistance data",
                "samples": [],
                "phenotypes": []
            }
        ]
        
        verified = verify_studies(["plant", "disease"], min_studies=1)
        
        assert len(verified) >= 1
        assert verified[0]["study_id"] == "ST001234"
        assert verified[0]["pre_challenge"] is True
        assert verified[0]["resistance_metadata"] is True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
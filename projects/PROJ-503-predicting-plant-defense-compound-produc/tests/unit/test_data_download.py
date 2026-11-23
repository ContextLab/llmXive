"""
Unit tests for data_download.py (T000).
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data_download import (
    validate_study_accession,
    check_herbivore_stress_geo,
    check_herbivore_stress_mw,
    E_DATASET
)

class TestValidation:
    def test_valid_geo_accession(self):
        assert validate_study_accession("GSE12345") is True
        assert validate_study_accession("GSE0") is True

    def test_invalid_geo_accession(self):
        assert validate_study_accession("GSE1234a") is False
        assert validate_study_accession("GSE") is False
        assert validate_study_accession("GS12345") is False

    def test_valid_mw_accession(self):
        assert validate_study_accession("ST00001") is True
        assert validate_study_accession("ST12345678") is True

    def test_invalid_mw_accession(self):
        assert validate_study_accession("ST0000a") is False
        assert validate_study_accession("S12345") is False

class TestKeywordMatching:
    def test_geo_herbivore_positive(self):
        metadata = {
            "title": "Response to herbivore feeding in Arabidopsis",
            "summary": "Study on insect chewing damage."
        }
        assert check_herbivore_stress_geo(metadata) is True

    def test_geo_herbivore_negative(self):
        metadata = {
            "title": "Drought stress response",
            "summary": "Water deficit effects."
        }
        assert check_herbivore_stress_geo(metadata) is False

    def test_mw_herbivore_positive(self):
        metadata = {
            "STUDY_TITLE": "Metabolomics of insect-attacked Solanum",
            "STUDY_ABSTRACT": "Analysis of defense compounds after wounding."
        }
        assert check_herbivore_stress_mw(metadata) is True

    def test_mw_herbivore_negative(self):
        metadata = {
            "STUDY_TITLE": "General metabolite profiling",
            "STUDY_ABSTRACT": "Untargeted metabolomics."
        }
        assert check_herbivore_stress_mw(metadata) is False

class TestE_DATASET:
    def test_exception_raised(self):
        with pytest.raises(E_DATASET) as exc_info:
            raise E_DATASET("Dataset not found")
        assert "Dataset not found" in str(exc_info.value)

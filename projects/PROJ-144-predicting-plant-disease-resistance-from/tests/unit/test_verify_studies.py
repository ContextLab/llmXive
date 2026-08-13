"""
Unit tests for verify_studies.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import STUDY_IDS, MW_BASE_URL
from research.verify_studies import (
    search_studies,
    get_study_metadata,
    check_pre_challenge_profiles,
    check_disease_resistance_metadata,
    verify_studies
)

def test_study_ids_defined():
    """Test that STUDY_IDS is defined and non-empty"""
    assert isinstance(STUDY_IDS, list)
    assert len(STUDY_IDS) > 0
    assert all(isinstance(sid, str) for sid in STUDY_IDS)

def test_base_url_format():
    """Test that MW_BASE_URL is correctly formatted"""
    assert MW_BASE_URL.startswith("http")
    assert "metabolomicsworkbench" in MW_BASE_URL.lower()

def test_check_pre_challenge_profiles_with_real_metadata():
    """Test pre-challenge profile detection with realistic metadata"""
    metadata_with_pre = {
        "study_title": "Plant response to pathogen at baseline and post-inoculation",
        "description": "Metabolomic profiles collected at pre-challenge and post-challenge time points"
    }
    assert check_pre_challenge_profiles(metadata_with_pre) is True

    metadata_without_pre = {
        "study_title": "General plant metabolomics",
        "description": "Unspecified sampling time"
    }
    assert check_pre_challenge_profiles(metadata_without_pre) is False

def test_check_disease_resistance_metadata():
    """Test disease resistance metadata detection"""
    metadata_with_resistance = {
        "study_title": "Disease resistance in Arabidopsis",
        "phenotype": "Resistance score to Pseudomonas syringae"
    }
    assert check_disease_resistance_metadata(metadata_with_resistance) is True

    metadata_without_resistance = {
        "study_title": "Metabolite profiling under drought",
        "phenotype": "Water potential"
    }
    assert check_disease_resistance_metadata(metadata_without_resistance) is False

def test_verify_studies_returns_list():
    """Test that verify_studies returns a list of dictionaries"""
    result = verify_studies()
    assert isinstance(result, list)
    if len(result) > 0:
        assert all(isinstance(item, dict) for item in result)
        # Check required keys
        for item in result:
            assert 'study_id' in item
            assert 'title' in item
            assert 'download_url' in item
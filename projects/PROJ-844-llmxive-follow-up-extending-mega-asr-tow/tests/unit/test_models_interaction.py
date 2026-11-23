"""
Unit tests specifically for interaction terms in code/models.py
"""
import pytest
import sys
import numpy as np
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from models import generate_interaction_terms, validate_hvcm_target

def test_generate_interaction_terms_comprehensive():
    """Test all interaction term types."""
    features = [
        {"snr_db": 10.0, "rt60": 0.5},
        {"snr_db": 20.0, "rt60": 0.8},
        {"snr_db": 5.0, "rt60": 0.2}
    ]
    
    result = generate_interaction_terms(features)
    
    assert len(result) == 3
    
    for i, sample in enumerate(result):
        # Check all expected keys exist
        assert "snr_db" in sample
        assert "rt60" in sample
        assert "snr_db_x_rt60" in sample
        assert "snr_db_sq" in sample
        assert "rt60_sq" in sample
        
        # Verify calculations
        snr = features[i]["snr_db"]
        rt60 = features[i]["rt60"]
        
        assert np.isclose(sample["snr_db_x_rt60"], snr * rt60)
        assert np.isclose(sample["snr_db_sq"], snr ** 2)
        assert np.isclose(sample["rt60_sq"], rt60 ** 2)

def test_validate_hvcm_target_missing_human_score():
    """Test HVCM validation with missing human score."""
    data = [
        {"clip_id": "1", "sss_collapse": 0.5, "human_score": None},
        {"clip_id": "2", "sss_collapse": 0.6, "human_score": 3}
    ]
    
    # Should raise ValueError or return False when human_score is missing
    with pytest.raises(ValueError):
        validate_hvcm_target(data)

def test_validate_hvcm_target_valid():
    """Test HVCM validation with valid data."""
    data = [
        {"clip_id": "1", "sss_collapse": 0.5, "human_score": 3},
        {"clip_id": "2", "sss_collapse": 0.6, "human_score": 4}
    ]
    
    # Should pass validation
    try:
        validate_hvcm_target(data)
    except ValueError:
        pytest.fail("validate_hvcm_target raised ValueError on valid data")

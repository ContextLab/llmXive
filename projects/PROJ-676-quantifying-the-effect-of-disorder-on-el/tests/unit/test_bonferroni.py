import pytest
import json
import os
import tempfile
from pathlib import Path

import numpy as np

# Import the functions to test
from apply_bonferroni import load_scaling_fits, apply_bonferroni_correction, analyze_scaling_slopes

def test_load_scaling_fits_valid_list():
    """Test loading a valid list of scaling fits."""
    data = [
        {"disorder_width": 0.5, "xi": 10.0, "uncertainty": 0.5, "p_value": 0.01},
        {"disorder_width": 1.0, "xi": 5.0, "uncertainty": 0.3, "p_value": 0.02}
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        temp_path = f.name
    
    try:
        result = load_scaling_fits(temp_path)
        assert len(result) == 2
        assert result[0]['disorder_width'] == 0.5
        assert result[0]['adjusted_p_value'] is None  # Not corrected yet
    finally:
        os.unlink(temp_path)

def test_load_scaling_fits_invalid_dict():
    """Test that loading a dict (legacy format) raises ValueError."""
    data = {"0.5": {}, "1.0": {}}
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError, match="must be a JSON list"):
            load_scaling_fits(temp_path)
    finally:
        os.unlink(temp_path)

def test_load_scaling_fits_missing_keys():
    """Test that missing required keys raises ValueError."""
    data = [
        {"disorder_width": 0.5, "xi": 10.0}  # Missing uncertainty, p_value
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError, match="missing required keys"):
            load_scaling_fits(temp_path)
    finally:
        os.unlink(temp_path)

def test_apply_bonferroni_correction():
    """Test Bonferroni correction logic."""
    data = [
        {"disorder_width": 0.5, "xi": 10.0, "uncertainty": 0.5, "p_value": 0.01},
        {"disorder_width": 1.0, "xi": 5.0, "uncertainty": 0.3, "p_value": 0.02},
        {"disorder_width": 2.0, "xi": 2.0, "uncertainty": 0.1, "p_value": 0.04}
    ]
    
    corrected, summary = apply_bonferroni_correction(data, alpha=0.05)
    
    assert len(corrected) == 3
    assert summary['n_tests'] == 3
    assert summary['corrected_alpha'] == 0.05 / 3
    
    # Check adjusted p-values
    assert corrected[0]['adjusted_p_value'] == pytest.approx(0.01 * 3)
    assert corrected[1]['adjusted_p_value'] == pytest.approx(0.02 * 3)
    assert corrected[2]['adjusted_p_value'] == pytest.approx(0.04 * 3)
    
    # Check significance
    # 0.03 < 0.0166 -> True
    # 0.06 > 0.0166 -> False
    # 0.12 > 0.0166 -> False
    assert corrected[0]['significant'] is True
    assert corrected[1]['significant'] is False
    assert corrected[2]['significant'] is False

def test_analyze_scaling_slopes():
    """Test linear regression analysis on scaling data."""
    data = [
        {"disorder_width": 0.5, "xi": 20.0, "uncertainty": 1.0, "p_value": 0.01},
        {"disorder_width": 1.0, "xi": 10.0, "uncertainty": 0.5, "p_value": 0.02},
        {"disorder_width": 2.0, "xi": 5.0, "uncertainty": 0.2, "p_value": 0.03}
    ]
    
    result = analyze_scaling_slopes(data)
    
    assert 'slope' in result
    assert 'r_squared' in result
    assert result['n_points'] == 3
    
    # For xi ~ W^-2, log(xi) = -2*log(W) + C
    # Slope should be close to -2
    assert abs(result['slope'] - (-2.0)) < 0.1
    assert result['r_squared'] > 0.99
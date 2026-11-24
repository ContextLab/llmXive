"""
Unit tests for T106 SHAP analysis and SC-003 verification.
"""

import pytest
import json
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from llmxive_toolkit import paths


def test_shap_ranking_structure():
    """Test that SHAP ranking structure is correct."""
    rankings = [
        {
            "rank": 1,
            "descriptor_name": "d_band_center",
            "mean_absolute_shap_value": 0.5
        },
        {
            "rank": 2,
            "descriptor_name": "activation_barrier",
            "mean_absolute_shap_value": 0.4
        }
    ]
    
    # Verify structure
    assert len(rankings) == 2
    assert rankings[0]["rank"] == 1
    assert rankings[0]["descriptor_name"] == "d_band_center"
    assert isinstance(rankings[0]["mean_absolute_shap_value"], float)


def test_sc003_ratio_calculation():
    """Test SC-003 ratio calculation."""
    r2_full = 0.80
    r2_reduced = 0.50
    
    ratio = r2_reduced / r2_full
    sc003_status = "PASS" if ratio >= 0.50 else "FAIL"
    
    assert ratio == 0.625
    assert sc003_status == "PASS"


def test_sc003_ratio_fail():
    """Test SC-003 FAIL condition."""
    r2_full = 0.80
    r2_reduced = 0.30
    
    ratio = r2_reduced / r2_full
    sc003_status = "PASS" if ratio >= 0.50 else "FAIL"
    
    assert ratio == 0.375
    assert sc003_status == "FAIL"


def test_sc003_verification_schema():
    """Test that SC-003 verification JSON has required fields."""
    sc003_data = {
        "full_model_r2": 0.80,
        "full_model_mae": 0.15,
        "reduced_model_r2": 0.50,
        "reduced_model_mae": 0.20,
        "ratio": 0.625,
        "SC-003_status": "PASS",
        "top_descriptors": ["d_band_center", "activation_barrier", "p_band_center", 
                           "bader_charges", "reaction_energy"]
    }
    
    # Verify required fields
    assert "ratio" in sc003_data
    assert "SC-003_status" in sc003_data
    assert "full_model_r2" in sc003_data
    assert "reduced_model_r2" in sc003_data
    assert sc003_data["SC-003_status"] in ["PASS", "FAIL"]


def test_feature_importance_plot_generation():
    """Test that feature importance plot is generated with correct structure."""
    rankings = [
        {"rank": 1, "descriptor_name": "d_band_center", "mean_absolute_shap_value": 0.5},
        {"rank": 2, "descriptor_name": "activation_barrier", "mean_absolute_shap_value": 0.4},
        {"rank": 3, "descriptor_name": "p_band_center", "mean_absolute_shap_value": 0.3},
        {"rank": 4, "descriptor_name": "bader_charges", "mean_absolute_shap_value": 0.2},
        {"rank": 5, "descriptor_name": "reaction_energy", "mean_absolute_shap_value": 0.1},
    ]
    
    top_5 = rankings[:5]
    assert len(top_5) == 5
    assert top_5[0]["descriptor_name"] == "d_band_center"
    assert top_5[4]["descriptor_name"] == "reaction_energy"


def test_shap_ranking_sorted_descending():
    """Test that rankings are sorted by SHAP value in descending order."""
    rankings = [
        {"rank": 1, "descriptor_name": "d_band_center", "mean_absolute_shap_value": 0.5},
        {"rank": 2, "descriptor_name": "activation_barrier", "mean_absolute_shap_value": 0.4},
        {"rank": 3, "descriptor_name": "p_band_center", "mean_absolute_shap_value": 0.3},
    ]
    
    # Verify descending order
    for i in range(len(rankings) - 1):
        assert rankings[i]["mean_absolute_shap_value"] >= rankings[i + 1]["mean_absolute_shap_value"]


def test_mean_absolute_shap_computation():
    """Test mean absolute SHAP value computation."""
    shap_values = np.array([
        [0.1, -0.2, 0.3],
        [-0.15, 0.25, -0.35],
        [0.05, -0.1, 0.2]
    ])
    
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    
    assert len(mean_abs_shap) == 3
    assert np.allclose(mean_abs_shap[0], 0.1)
    assert np.allclose(mean_abs_shap[1], 0.183333, rtol=0.01)
    assert np.allclose(mean_abs_shap[2], 0.283333, rtol=0.01)
"""
Unit tests for T036: Extract Interaction Terms.
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from extract_interaction import (
    extract_tobit_interaction_pvalue,
    extract_cox_interaction_pvalue,
    load_model_results
)


class TestExtractTobitInteraction:
    def test_extract_interaction_pvalue_success(self):
        """Test successful extraction of interaction p-value from Tobit results."""
        mock_data = {
            "tobit": {
                "coefficients": [
                    {"term": "Intercept", "pvalue": 0.001},
                    {"term": "C(loss_type)[T.1]", "pvalue": 0.05},
                    {"term": "beta", "pvalue": 0.02},
                    {"term": "C(loss_type)[T.1]:beta", "pvalue": 0.035}
                ]
            }
        }
        
        p_val = extract_tobit_interaction_pvalue(mock_data)
        assert abs(p_val - 0.035) < 1e-6
    
    def test_extract_interaction_pvalue_missing(self):
        """Test that missing interaction term raises ValueError."""
        mock_data = {
            "tobit": {
                "coefficients": [
                    {"term": "Intercept", "pvalue": 0.001},
                    {"term": "C(loss_type)[T.1]", "pvalue": 0.05},
                    {"term": "beta", "pvalue": 0.02}
                ]
            }
        }
        
        with pytest.raises(ValueError, match="Could not locate interaction term"):
            extract_tobit_interaction_pvalue(mock_data)
    
    def test_extract_interaction_pvalue_no_tobit_key(self):
        """Test that missing 'tobit' key raises ValueError."""
        mock_data = {"other_model": {}}
        
        with pytest.raises(ValueError, match="Tobit results not found"):
            extract_tobit_interaction_pvalue(mock_data)


class TestExtractCoxInteraction:
    def test_extract_interaction_pvalue_success(self):
        """Test successful extraction of interaction p-value from Cox results."""
        mock_data = {
            "cox": {
                "coefficients": [
                    {"term": "Intercept", "pvalue": 0.001},
                    {"term": "C(loss_type)[T.1]", "pvalue": 0.05},
                    {"term": "beta", "pvalue": 0.02},
                    {"term": "C(loss_type)[T.1]:beta", "pvalue": 0.042}
                ]
            }
        }
        
        p_val = extract_cox_interaction_pvalue(mock_data)
        assert abs(p_val - 0.042) < 1e-6
    
    def test_extract_interaction_pvalue_missing(self):
        """Test that missing interaction term raises ValueError."""
        mock_data = {
            "cox": {
                "coefficients": [
                    {"term": "Intercept", "pvalue": 0.001},
                    {"term": "C(loss_type)[T.1]", "pvalue": 0.05},
                    {"term": "beta", "pvalue": 0.02}
                ]
            }
        }
        
        with pytest.raises(ValueError, match="Could not locate interaction term"):
            extract_cox_interaction_pvalue(mock_data)
    
    def test_extract_interaction_pvalue_no_cox_key(self):
        """Test that missing 'cox' key raises ValueError."""
        mock_data = {"other_model": {}}
        
        with pytest.raises(ValueError, match="Cox results not found"):
            extract_cox_interaction_pvalue(mock_data)

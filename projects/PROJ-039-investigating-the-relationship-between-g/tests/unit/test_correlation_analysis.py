"""
Unit tests for correlation_analysis.py (T022).
"""
import os
import json
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Mock the project root for testing
import sys
from unittest.mock import patch

# Import functions to test
# We assume the module is importable as 'correlation_analysis'
# For unit testing, we might need to adjust imports if not in path
# Here we assume the test runs with code/ in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from correlation_analysis import (
    load_stratum_features,
    select_top_taxa,
    compute_spearman_correlations,
    apply_fdr_correction,
    FDR_THRESHOLD,
    TOP_N_TAXA
)

def test_select_top_taxa():
    """Test that select_top_taxa correctly identifies the top N taxa."""
    # Create dummy data
    data = [
        {
            "stratum_id": "S1",
            "mean_alpha_power": 10.0,
            "n_subjects": 10,
            "clr_taxa_abundances": {"TaxonA": 1.0, "TaxonB": 0.5, "TaxonC": 0.1}
        },
        {
            "stratum_id": "S2",
            "mean_alpha_power": 12.0,
            "n_subjects": 10,
            "clr_taxa_abundances": {"TaxonA": 2.0, "TaxonB": 1.0, "TaxonC": 0.2}
        },
        {
            "stratum_id": "S3",
            "mean_alpha_power": 11.0,
            "n_subjects": 10,
            "clr_taxa_abundances": {"TaxonA": 1.5, "TaxonB": 0.8, "TaxonC": 0.15}
        }
    ]
    df = pd.DataFrame(data)
    
    top_taxa = select_top_taxa(df, n=2)
    
    # Expected order: TaxonA (mean 1.5), TaxonB (mean 0.76), TaxonC (mean 0.15)
    assert top_taxa[0] == "TaxonA"
    assert top_taxa[1] == "TaxonB"

def test_compute_spearman_correlations():
    """Test Spearman correlation calculation."""
    # Create data with known correlation
    # TaxonA increases with AlphaPower
    data = [
        {"stratum_id": "S1", "mean_alpha_power": 10.0, "n_subjects": 10, "clr_taxa_abundances": {"TaxonA": 1.0}},
        {"stratum_id": "S2", "mean_alpha_power": 20.0, "n_subjects": 10, "clr_taxa_abundances": {"TaxonA": 2.0}},
        {"stratum_id": "S3", "mean_alpha_power": 30.0, "n_subjects": 10, "clr_taxa_abundances": {"TaxonA": 3.0}},
    ]
    df = pd.DataFrame(data)
    
    results = compute_spearman_correlations(df, ["TaxonA"])
    
    assert len(results) == 1
    assert results[0]["taxon"] == "TaxonA"
    # Perfect positive correlation
    assert results[0]["rho"] == 1.0
    assert results[0]["p_value"] == 0.0 # Or very close to 0

def test_apply_fdr_correction():
    """Test FDR correction logic."""
    results = [
        {"taxon": "A", "p_value": 0.01},
        {"taxon": "B", "p_value": 0.05},
        {"taxon": "C", "p_value": 0.20},
        {"taxon": "D", "p_value": 0.001}
    ]
    
    corrected = apply_fdr_correction(results, threshold=0.1)
    
    assert all("q_value" in r for r in corrected)
    assert all("significant" in r for r in corrected)
    
    # D and A should likely be significant
    assert corrected[3]["significant"] == True # p=0.001
    assert corrected[0]["significant"] == True # p=0.01 (likely)
    assert corrected[2]["significant"] == False # p=0.20

def test_load_stratum_features_with_string_dict():
    """Test loading CSV where clr_taxa_abundances is a JSON string."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("stratum_id,mean_alpha_power,n_subjects,clr_taxa_abundances\n")
        f.write('S1,10.0,10,"{\"TaxonA\": 1.0, \"TaxonB\": 0.5}"\n')
        temp_path = f.name
    
    try:
        df = load_stratum_features(temp_path)
        assert isinstance(df['clr_taxa_abundances'].iloc[0], dict)
        assert df['clr_taxa_abundances'].iloc[0]['TaxonA'] == 1.0
    finally:
        os.unlink(temp_path)
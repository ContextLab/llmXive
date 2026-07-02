"""
Integration tests for Schema Validation (T004)
Tests the full flow of validating artifacts created by the pipeline.
"""
import pytest
import pandas as pd
import json
import tempfile
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from schema_validator import validate_artifacts

def test_full_artifact_validation():
    """Test validation of a complete set of generated artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create valid input files
        m_df = pd.DataFrame({
            "subject_id": ["S1", "S2"],
            "age": [25.0, 30.0],
            "sex": ["M", "F"],
            "bmi": [22.0, 24.0],
            "taxa_A": [0.1, 0.2]
        })
        m_path = tmpdir / "microbiome_features.csv"
        m_df.to_csv(m_path, index=False)
        
        e_df = pd.DataFrame({
            "subject_id": ["E1", "E2"],
            "age": [26.0, 31.0],
            "sex": ["M", "F"],
            "alpha_power": [10.5, 12.0]
        })
        e_path = tmpdir / "eeg_features.csv"
        e_df.to_csv(e_path, index=False)
        
        # Create valid matched pairs
        p_df = pd.DataFrame({
            "microbiome_subject_id": ["S1"],
            "eeg_subject_id": ["E1"],
            "age_diff": [1.0],
            "sex_match": [True],
            "bmi_diff": [0.5],
            "matching_score": [0.9]
        })
        p_path = tmpdir / "matched_pairs.csv"
        p_df.to_csv(p_path, index=False)
        
        # Create valid results
        results = {
            "path_selected": "Path A (Matching)",
            "n_pairs": 1,
            "statistical_test": "Spearman",
            "p_value": 0.03,
            "q_value": 0.05,
            "permutation_passed": True,
            "disclaimer": "Note: This analysis is associational only; no causal inference is made."
        }
        r_path = tmpdir / "analysis_results.json"
        with open(r_path, 'w') as f:
            json.dump(results, f)
        
        # Run validation
        success = validate_artifacts(
            microbiome_path=str(m_path),
            eeg_path=str(e_path),
            matched_pairs_path=str(p_path),
            results_path=str(r_path)
        )
        
        assert success is True

def test_missing_required_artifact_fields():
    """Test validation failure when required fields are missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create valid inputs
        m_df = pd.DataFrame({
            "subject_id": ["S1"],
            "age": [25.0],
            "sex": ["M"],
            "bmi": [22.0],
            "taxa_A": [0.1]
        })
        m_path = tmpdir / "microbiome_features.csv"
        m_df.to_csv(m_path, index=False)
        
        e_df = pd.DataFrame({
            "subject_id": ["E1"],
            "age": [26.0],
            "sex": ["M"],
            "alpha_power": [10.5]
        })
        e_path = tmpdir / "eeg_features.csv"
        e_df.to_csv(e_path, index=False)
        
        # Create invalid results (missing disclaimer)
        results = {
            "path_selected": "Path A (Matching)",
            "n_pairs": 1,
            "statistical_test": "Spearman",
            "p_value": 0.03,
            "q_value": 0.05,
            "permutation_passed": True
        }
        r_path = tmpdir / "analysis_results.json"
        with open(r_path, 'w') as f:
            json.dump(results, f)
        
        success = validate_artifacts(
            microbiome_path=str(m_path),
            eeg_path=str(e_path),
            results_path=str(r_path)
        )
        
        assert success is False
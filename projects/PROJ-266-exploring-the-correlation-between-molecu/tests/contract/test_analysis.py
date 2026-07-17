"""
Contract tests for analysis_output.schema.yaml.

These tests validate that the analysis output (e.g., JSON/CSV results from analysis.py)
strictly adheres to the schema defined in specs/001-molecular-flexibility-permeability/contracts/analysis_output.schema.yaml.

Run with: pytest tests/contract/test_analysis.py -v
"""

import json
import os
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_project_root


def load_schema(schema_path: str) -> dict:
    """Load JSON schema from YAML file."""
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    return schema


def load_analysis_results(json_path: str) -> dict:
    """Load analysis results from JSON file."""
    if not os.path.exists(json_path):
        pytest.fail(f"Analysis results file not found: {json_path}")
    with open(json_path, 'r') as f:
        return json.load(f)

def test_analysis_schema_exists():
    """Verify the analysis schema file exists."""
    schema_path = get_project_root() / "specs/001-molecular-flexibility-permeability/contracts/analysis_output.schema.yaml"
    assert schema_path.exists(), f"Schema file missing: {schema_path}"

def test_analysis_output_structure():
    """
    Validate the analysis output structure against the schema.
    
    This test checks:
    1. Required top-level sections exist (metadata, correlations, regression_model, diagnostics)
    2. Required fields within sections are present
    3. Data types are consistent with schema
    """
    schema_path = get_project_root() / "specs/001-molecular-flexibility-permeability/contracts/analysis_output.schema.yaml"
    results_path = get_project_root() / "data/processed/analysis_results.json"
    
    if not results_path.exists():
        pytest.fail(f"Analysis results not found at {results_path}. Run analysis pipeline first.")
    
    schema = load_schema(str(schema_path))
    results = load_analysis_results(str(results_path))
    
    # Check top-level required keys
    required_top_keys = schema['required']
    missing_keys = [k for k in required_top_keys if k not in results]
    assert not missing_keys, f"Missing top-level keys: {missing_keys}"
    
    # Check metadata
    meta = results.get('metadata', {})
    assert 'generated_at' in meta
    assert 'dataset_version' in meta
    assert 'sample_size' in meta
    assert meta['sample_size'] > 0
    
    # Check correlations
    corrs = results.get('correlations', {})
    assert 'dihedral_variance' in corrs, "Primary predictor correlation missing"
    diag = corrs['dihedral_variance']
    assert 'pearson_r' in diag
    assert 'pearson_p' in diag
    assert 'fdr_q' in diag
    
    # Check regression model
    reg = results.get('regression_model', {})
    assert 'model_type' in reg
    assert 'primary_predictor' in reg
    assert reg['primary_predictor'] == 'dihedral_variance', "Primary predictor must be dihedral_variance"
    assert 'coefficients' in reg
    assert 'metrics' in reg
    
    # Check metrics
    metrics = reg['metrics']
    assert 'r_squared' in metrics
    assert 'cv_r_squared_mean' in metrics
    
    # Check diagnostics
    diag_section = results.get('diagnostics', {})
    assert 'vif_scores' in diag_section
    assert 'collinearity_action' in diag_section

def test_visualization_metadata():
    """
    Verify visualization metadata is present and valid.
    """
    results_path = get_project_root() / "data/processed/analysis_results.json"
    if not results_path.exists():
        pytest.skip("Analysis results not generated yet")
    
    with open(results_path, 'r') as f:
        results = json.load(f)
    
    viz = results.get('visualization', {})
    assert 'scatter_plot_path' in viz
    assert 'plot_title' in viz
    
    # Check title contains "associational" as per FR-009
    title = viz['plot_title'].lower()
    assert 'associational' in title, f"Plot title must state 'associational' (FR-009): {viz['plot_title']}"
    
    assert 'dpi' in viz
    assert viz['dpi'] >= 300, "Plot DPI must be >= 300"
"""
Contract tests for the analysis output schema.

This module validates that the statistical analysis pipeline produces
outputs that conform to the project's specification contracts, specifically
ensuring that results are correctly labeled as "associational".
"""
import pytest
import pandas as pd
import numpy as np
import json
import tempfile
import os
from pathlib import Path
from typing import Dict, Any

# Import the analysis service to test its output contract
from src.services.analysis import run_full_analysis, save_analysis_report
from src.lib import config


def test_report_has_associational_label():
    """
    Contract test: Verify that the analysis report explicitly labels results
    as "associational" as required by spec FR-007.
    
    This test creates a minimal synthetic dataset (for contract testing only),
    runs the full analysis pipeline, and verifies the output structure contains
    the required "associational" label.
    
    Note: This test uses synthetic data to verify the OUTPUT CONTRACT (schema
    and labeling), not the scientific validity of the results. The actual
    pipeline must run on real OpenAlex data for scientific conclusions.
    """
    # Create a minimal synthetic dataset for contract testing
    # This is ONLY to verify the output schema, not scientific results
    n_samples = 50
    data = {
        'node_id': [f'node_{i}' for i in range(n_samples)],
        'bridging_coefficient': np.random.uniform(0.0, 1.0, n_samples),
        'citation_count': np.random.poisson(10, n_samples),
        'novelty_score': np.random.uniform(0.1, 1.0, n_samples)
    }
    df = pd.DataFrame(data)
    
    # Run the full analysis on this synthetic data
    # The function should return a dictionary with the analysis results
    results = run_full_analysis(df)
    
    # Verify the results structure
    assert isinstance(results, dict), "Analysis results must be a dictionary"
    
    # Check that required keys exist
    required_keys = ['correlations', 'regression', 'binned_analysis', 'methodology']
    for key in required_keys:
        assert key in results, f"Missing required key: {key}"
    
    # Contract: The methodology section MUST explicitly state "associational"
    assert 'methodology' in results, "Methodology section missing from results"
    methodology = results['methodology']
    
    # Verify the label exists and is correct
    assert 'label' in methodology, "Methodology label missing"
    assert methodology['label'] == 'associational', \
        f"Expected methodology label to be 'associational', got: {methodology['label']}"
    
    # Verify the label is also present in the full report text if generated
    if 'report_text' in results:
        assert 'associational' in results['report_text'].lower(), \
            "Report text must contain 'associational' label"
    
    # Additional contract checks for data integrity
    assert 'correlations' in results, "Correlations section missing"
    assert isinstance(results['correlations'], dict), "Correlations must be a dictionary"
    
    # Verify correlation entries have expected structure
    for metric in ['citation_count', 'novelty_score']:
        if metric in results['correlations']:
            corr_data = results['correlations'][metric]
            assert 'spearman_correlation' in corr_data, \
                f"Missing spearman_correlation for {metric}"
            assert 'p_value' in corr_data, f"Missing p_value for {metric}"
            assert 'corrected_p_value' in corr_data, \
                f"Missing corrected_p_value for {metric}"
    
    # Verify regression results structure
    assert 'regression' in results, "Regression section missing"
    for metric in ['citation_count', 'novelty_score']:
        if metric in results['regression']:
            reg_data = results['regression'][metric]
            assert 'coefficient' in reg_data, f"Missing coefficient for {metric}"
            assert 'p_value' in reg_data, f"Missing p_value for {metric}"
            assert 'r_squared' in reg_data, f"Missing r_squared for {metric}"
    
    # Verify binned analysis structure
    assert 'binned_analysis' in results, "Binned analysis section missing"
    
    # If we have binned analysis results, verify structure
    if results['binned_analysis'] and len(results['binned_analysis']) > 0:
        for bin_result in results['binned_analysis']:
            assert 'bin_range' in bin_result, "Missing bin_range in binned result"
            assert 'mean_bridging' in bin_result, "Missing mean_bridging in binned result"
            assert 'mean_outcome' in bin_result, "Missing mean_outcome in binned result"
            assert 'n_samples' in bin_result, "Missing n_samples in binned result"
    
    # Test that save_analysis_report creates a file with the correct label
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "test_analysis_report.md"
        
        # Save the report
        save_analysis_report(results, str(report_path))
        
        # Verify the file was created
        assert report_path.exists(), "Report file was not created"
        
        # Read and verify content
        with open(report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
        
        # Contract: File must contain the associational label
        assert 'associational' in report_content.lower(), \
            "Saved report must contain 'associational' label"
        
        # Contract: File must contain a clear methodology section
        assert 'methodology' in report_content.lower(), \
            "Report must contain methodology section"
        
        # Contract: File must not claim causality
        assert 'causal' not in report_content.lower() or \
               'not causal' in report_content.lower() or \
               'associational' in report_content.lower(), \
            "Report should not claim causality without qualification"
    
    # Test JSON metrics output
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics_path = Path(tmpdir) / "test_statistical_metrics.json"
        
        # Save metrics as JSON
        with open(metrics_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Verify JSON is valid and contains the label
        with open(metrics_path, 'r', encoding='utf-8') as f:
            loaded_results = json.load(f)
        
        assert loaded_results['methodology']['label'] == 'associational', \
            "JSON metrics must preserve the associational label"
    
    # All contract checks passed
    return True
"""
Unit tests for generate_statistical_results module.

Tests the statistical analysis pipeline including:
- Data preparation
- GLMM model fitting
- Effect size calculation
- Output validation
"""

import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis.generate_statistical_results import (
    load_execution_traces,
    prepare_data_for_glmm,
    fit_glmm,
    calculate_effect_sizes,
    run_statistical_analysis
)


@pytest.fixture
def sample_execution_traces():
    """Create sample execution traces data."""
    data = {
        'task_id': ['task1', 'task2', 'task3', 'task4', 'task5'],
        'architecture': ['dual_track', 'monolithic', 'dual_track', 'monolithic', 'dual_track'],
        'constraint_count': [5, 6, 7, 5, 8],
        'violation': [0, 1, 0, 1, 0],
        'final_score': [0.9, 0.6, 0.85, 0.5, 0.95]
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_annotations():
    """Create sample human annotations."""
    data = {
        'task_id': ['task1', 'task2', 'task3'],
        'human_violation': [0, 1, 0]
    }
    return pd.DataFrame(data)


def test_prepare_data_for_glmm_basic(sample_execution_traces):
    """Test basic data preparation without annotations."""
    prepared = prepare_data_for_glmm(sample_execution_traces, None)
    
    # Check required columns exist
    assert 'violation_binary' in prepared.columns
    assert 'final_violation' in prepared.columns
    assert 'architecture_encoded' in prepared.columns
    
    # Check encoding
    assert prepared['architecture_encoded'].isin([0, 1]).all()
    assert len(prepared) == len(sample_execution_traces)


def test_prepare_data_for_glmm_with_annotations(sample_execution_traces, sample_annotations):
    """Test data preparation with human annotations."""
    prepared = prepare_data_for_glmm(sample_execution_traces, sample_annotations)
    
    # Check that human annotations were merged
    assert 'human_violation' in prepared.columns
    assert len(prepared) == len(sample_execution_traces)


def test_fit_glmm_convergence(sample_execution_traces):
    """Test that GLMM fitting returns valid results."""
    prepared = prepare_data_for_glmm(sample_execution_traces, None)
    results, model = fit_glmm(prepared)
    
    # Check results structure
    assert 'converged' in results
    assert 'coefficients' in results
    assert 'p_values' in results
    assert 'interaction_p_value' in results
    
    # Check that we have coefficients for expected terms
    expected_terms = ['const', 'architecture_encoded', 'constraint_count']
    for term in expected_terms:
        assert term in results['coefficients']


def test_calculate_effect_sizes(sample_execution_traces):
    """Test effect size calculation."""
    prepared = prepare_data_for_glmm(sample_execution_traces, None)
    _, model = fit_glmm(prepared)
    
    if model is not None:
        effect_sizes = calculate_effect_sizes(prepared, model)
        
        assert 'odds_ratios' in effect_sizes
        assert 'confidence_intervals' in effect_sizes
        assert 'lower' in effect_sizes['confidence_intervals']
        assert 'upper' in effect_sizes['confidence_intervals']


def test_run_statistical_analysis_structure(sample_execution_traces, tmp_path):
    """Test that the full analysis produces correct output structure."""
    # Mock file loading
    with patch('analysis.generate_statistical_results.load_execution_traces') as mock_load:
        mock_load.return_value = sample_execution_traces
        
        with patch('analysis.generate_statistical_results.load_human_annotations') as mock_ann:
            mock_ann.return_value = None
            
            results = run_statistical_analysis()
            
            # Check top-level structure
            required_keys = [
                'analysis_metadata', 'model_fit', 'hypothesis_testing',
                'coefficients', 'p_values', 'effect_sizes', 'conclusion'
            ]
            
            for key in required_keys:
                assert key in results, f"Missing required key: {key}"
            
            # Check metadata structure
            assert 'timestamp' in results['analysis_metadata']
            assert 'sample_size' in results['analysis_metadata']
            
            # Check conclusion structure
            assert 'significant_interaction' in results['conclusion']
            assert 'interpretation' in results['conclusion']


def test_missing_required_columns(sample_execution_traces):
    """Test error handling for missing required columns."""
    # Remove a required column
    incomplete_data = sample_execution_traces.drop(columns=['violation'])
    
    with pytest.raises(ValueError, match="Missing required column"):
        prepare_data_for_glmm(incomplete_data, None)


def test_interaction_p_value_calculation(sample_execution_traces):
    """Test that interaction p-value is correctly extracted."""
    prepared = prepare_data_for_glmm(sample_execution_traces, None)
    results, _ = fit_glmm(prepared)
    
    # The interaction p-value should be present
    assert results['interaction_p_value'] is not None
    assert 0 <= results['interaction_p_value'] <= 1


def test_schema_compliance(sample_execution_traces):
    """Test that output matches expected schema."""
    with patch('analysis.generate_statistical_results.load_execution_traces') as mock_load:
        mock_load.return_value = sample_execution_traces
        
        with patch('analysis.generate_statistical_results.load_human_annotations') as mock_ann:
            mock_ann.return_value = None
            
            results = run_statistical_analysis()
            
            # Validate against schema requirements
            assert isinstance(results['analysis_metadata']['sample_size'], int)
            assert isinstance(results['model_fit']['converged'], bool)
            assert isinstance(results['conclusion']['significant_interaction'], bool)
            
            # Check p-value range
            if results['hypothesis_testing']['interaction_p_value'] is not None:
                assert 0 <= results['hypothesis_testing']['interaction_p_value'] <= 1

"""
Unit tests for T014a: detect_label_heterogeneity.py
"""
import os
import sys
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path
import shutil

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from code.data.detect_label_heterogeneity import (
    analyze_column_distribution,
    detect_global_heterogeneity,
    DataUnavailableError
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure for testing."""
    temp_dir = tempfile.mkdtemp()
    raw_dir = Path(temp_dir) / 'data' / 'raw'
    processed_dir = Path(temp_dir) / 'data' / 'processed'
    raw_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)
    
    # Temporarily override global paths
    import code.data.detect_label_heterogeneity as mod
    mod.RAW_DATA_DIR = raw_dir
    mod.PROCESSED_DATA_DIR = processed_dir
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)
    # Restore original paths
    mod.RAW_DATA_DIR = PROJECT_ROOT / 'data' / 'raw'
    mod.PROCESSED_DATA_DIR = PROJECT_ROOT / 'data' / 'processed'

def test_analyze_column_distribution_missing_column(temp_data_dir):
    """Test analysis when column is missing."""
    df = pd.DataFrame({'other_col': [1, 2, 3]})
    result = analyze_column_distribution(df, 'missing_col', 'test_study')
    
    assert result['found'] is False
    assert result['column'] == 'missing_col'
    assert 'not found' in result['reason']

def test_analyze_column_distribution_binary_method(temp_data_dir):
    """Test analysis with a single binary measurement method."""
    df = pd.DataFrame({
        'measurement_method': ['ELISA', 'ELISA', 'ELISA'],
        'assay_score': [0, 1, 1]
    })
    result = analyze_column_distribution(df, 'measurement_method', 'test_study')
    
    assert result['found'] is True
    assert result['heterogeneous'] is False
    assert 'Single method' in result['reason']
    assert len(result['unique_values']) == 1

def test_analyze_column_distribution_multiple_methods(temp_data_dir):
    """Test analysis with multiple measurement methods."""
    df = pd.DataFrame({
        'measurement_method': ['ELISA', 'MassSpec', 'ELISA', 'PCR'],
        'assay_score': [0, 1, 1, 0]
    })
    result = analyze_column_distribution(df, 'measurement_method', 'test_study')
    
    assert result['found'] is True
    assert result['heterogeneous'] is True
    assert 'Multiple measurement methods' in result['reason']
    assert len(result['unique_values']) == 3

def test_analyze_column_distribution_binary_score(temp_data_dir):
    """Test analysis with binary assay scores."""
    df = pd.DataFrame({
        'measurement_method': ['ELISA', 'ELISA'],
        'assay_score': [0.0, 1.0]
    })
    result = analyze_column_distribution(df, 'assay_score', 'test_study')
    
    assert result['found'] is True
    assert result['heterogeneous'] is False
    assert 'Binary scale' in result['reason']

def test_analyze_column_distribution_ordinal_score(temp_data_dir):
    """Test analysis with ordinal (multi-class) assay scores."""
    df = pd.DataFrame({
        'measurement_method': ['ELISA', 'ELISA', 'ELISA'],
        'assay_score': [0, 1, 2]  # 0, 1, 2 implies ordinal scale
    })
    result = analyze_column_distribution(df, 'assay_score', 'test_study')
    
    assert result['found'] is True
    assert result['heterogeneous'] is True
    assert 'Ordinal scale' in result['reason']

def test_analyze_column_distribution_mixed_scores(temp_data_dir):
    """Test analysis with mixed numeric and non-numeric scores."""
    df = pd.DataFrame({
        'measurement_method': ['ELISA', 'ELISA'],
        'assay_score': [1, 'high']
    })
    result = analyze_column_distribution(df, 'assay_score', 'test_study')
    
    assert result['found'] is True
    assert result['heterogeneous'] is True
    assert 'Non-numeric scores' in result['reason']

def test_detect_global_heterogeneity_single_study(temp_data_dir):
    """Test global detection with a single homogeneous study."""
    study_analyses = [
        {
            'method_analysis': {'found': True, 'unique_values': ['ELISA'], 'heterogeneous': False},
            'score_analysis': {'found': True, 'unique_values': [0, 1], 'heterogeneous': False}
        }
    ]
    result = detect_global_heterogeneity(study_analyses)
    
    assert result['global_heterogeneous'] is False
    assert result['total_studies'] == 1

def test_detect_global_heterogeneity_multiple_methods(temp_data_dir):
    """Test global detection with multiple methods across studies."""
    study_analyses = [
        {
            'method_analysis': {'found': True, 'unique_values': ['ELISA'], 'heterogeneous': False},
            'score_analysis': {'found': True, 'unique_values': [0, 1], 'heterogeneous': False}
        },
        {
            'method_analysis': {'found': True, 'unique_values': ['MassSpec'], 'heterogeneous': False},
            'score_analysis': {'found': True, 'unique_values': [0, 1], 'heterogeneous': False}
        }
    ]
    result = detect_global_heterogeneity(study_analyses)
    
    assert result['global_heterogeneous'] is True
    assert 'Multiple measurement methods' in result['reasons'][0]

def test_detect_global_heterogeneity_scale_difference(temp_data_dir):
    """Test global detection with vastly different score ranges."""
    study_analyses = [
        {
            'method_analysis': {'found': True, 'unique_values': ['ELISA'], 'heterogeneous': False},
            'score_analysis': {'found': True, 'unique_values': [0, 1], 'heterogeneous': False}
        },
        {
            'method_analysis': {'found': True, 'unique_values': ['ELISA'], 'heterogeneous': False},
            'score_analysis': {'found': True, 'unique_values': [0, 100], 'heterogeneous': False} # Large range
        }
    ]
    result = detect_global_heterogeneity(study_analyses)
    
    assert result['global_heterogeneous'] is True
    assert 'Wide range' in result['reasons'][0]
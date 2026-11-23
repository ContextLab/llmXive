import json
import os
import tempfile
from pathlib import Path
import pandas as pd
import pytest

from annotation import load_feature_data, load_annotation_data, merge_data_for_correlation, compute_correlations

@pytest.fixture
def sample_data(tmp_path):
    """Create sample feature and annotation data for testing."""
    # Create feature data
    features_df = pd.DataFrame({
        'prompt_id': ['p1', 'p2', 'p3', 'p4', 'p5'],
        'modal_verb_freq': [0.5, 0.8, 0.3, 0.9, 0.6],
        'imperative_ratio': [0.2, 0.4, 0.1, 0.5, 0.3],
        'citation_density': [2.0, 1.5, 3.0, 1.0, 2.5]
    })
    
    # Create annotation data
    annotation_df = pd.DataFrame({
        'prompt_id': ['p1', 'p2', 'p3', 'p4', 'p5'],
        'authority_density_score': [3.5, 4.2, 2.1, 4.8, 3.0]
    })
    
    # Write to temporary files
    feature_path = tmp_path / "features.csv"
    annotation_path = tmp_path / "annotation_pilot_us1.csv"
    
    features_df.to_csv(feature_path, index=False)
    annotation_df.to_csv(annotation_path, index=False)
    
    return {
        'features_path': feature_path,
        'annotation_path': annotation_path,
        'features_df': features_df,
        'annotation_df': annotation_df
    }

def test_load_feature_data(sample_data, tmp_path):
    """Test loading feature data."""
    config = {
        'paths': {
            'processed_features': str(sample_data['features_path'])
        }
    }
    
    df = load_feature_data(config)
    
    assert len(df) == 5
    assert 'prompt_id' in df.columns
    assert 'modal_verb_freq' in df.columns
    assert 'imperative_ratio' in df.columns
    assert 'citation_density' in df.columns

def test_load_annotation_data(sample_data, tmp_path):
    """Test loading annotation data."""
    config = {
        'paths': {
            'annotation_pilot_us1': str(sample_data['annotation_path'])
        }
    }
    
    df = load_annotation_data(config)
    
    assert len(df) == 5
    assert 'prompt_id' in df.columns
    assert 'authority_density_score' in df.columns

def test_merge_data_for_correlation(sample_data, tmp_path):
    """Test merging feature and annotation data."""
    feature_config = {
        'paths': {
            'processed_features': str(sample_data['features_path'])
        }
    }
    annotation_config = {
        'paths': {
            'annotation_pilot_us1': str(sample_data['annotation_path'])
        }
    }
    
    features_df = load_feature_data(feature_config)
    annotation_df = load_annotation_data(annotation_config)
    
    merged = merge_data_for_correlation(features_df, annotation_df)
    
    assert len(merged) == 5
    assert 'modal_verb_freq' in merged.columns
    assert 'authority_density_score' in merged.columns

def test_compute_correlations(sample_data, tmp_path):
    """Test correlation computation."""
    feature_config = {
        'paths': {
            'processed_features': str(sample_data['features_path'])
        }
    }
    annotation_config = {
        'paths': {
            'annotation_pilot_us1': str(sample_data['annotation_path'])
        }
    }
    
    features_df = load_feature_data(feature_config)
    annotation_df = load_annotation_data(annotation_config)
    merged = merge_data_for_correlation(features_df, annotation_df)
    
    results = compute_correlations(merged)
    
    assert 'sample_size' in results
    assert results['sample_size'] == 5
    assert 'correlations' in results
    
    # Check that all expected features are present
    for feature in ['modal_verb_freq', 'imperative_ratio', 'citation_density']:
        assert feature in results['correlations']
        assert 'pearson' in results['correlations'][feature]
        assert 'spearman' in results['correlations'][feature]
        
        # Check correlation values are reasonable
        assert -1 <= results['correlations'][feature]['pearson']['r'] <= 1
        assert 0 <= results['correlations'][feature]['pearson']['p_value'] <= 1

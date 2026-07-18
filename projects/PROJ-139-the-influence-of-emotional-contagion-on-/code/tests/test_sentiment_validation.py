"""
Tests for the sentiment validation module.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from code.data.sentiment_validation import (
    validate_vader_against_corpus,
    compute_bootstrapped_ci,
    generate_validation_justification
)

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    data = {
        'comment_id': ['c1', 'c2', 'c3', 'c4', 'c5'],
        'text': [
            'This is great!',
            'This is terrible.',
            'It is okay.',
            'I love this!',
            'I hate this.'
        ],
        'vader_label': ['positive', 'negative', 'neutral', 'positive', 'negative']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_annotations():
    """Create sample annotations for testing."""
    return [
        {'comment_id': 'c1', 'label': 'positive'},
        {'comment_id': 'c2', 'label': 'negative'},
        {'comment_id': 'c3', 'label': 'neutral'},
        {'comment_id': 'c4', 'label': 'positive'},
        {'comment_id': 'c5', 'label': 'negative'}
    ]

def test_validate_vader_against_corpus_perfect_agreement(sample_dataframe, sample_annotations):
    """Test validation with perfect agreement."""
    metrics = validate_vader_against_corpus(sample_dataframe, sample_annotations)
    assert metrics['overall_agreement'] == 1.0
    assert metrics['total_samples'] == 5

def test_validate_vader_against_corpus_partial_agreement(sample_dataframe, sample_annotations):
    """Test validation with partial agreement."""
    # Modify one annotation to create disagreement
    sample_annotations[0]['label'] = 'negative'
    metrics = validate_vader_against_corpus(sample_dataframe, sample_annotations)
    assert metrics['overall_agreement'] < 1.0
    assert metrics['total_samples'] == 5

def test_compute_bootstrapped_ci(sample_dataframe, sample_annotations):
    """Test bootstrapped confidence interval computation."""
    ci_results = compute_bootstrapped_ci(sample_dataframe, sample_annotations, n_iterations=100)
    assert 'kappa_ci_lower' in ci_results
    assert 'kappa_ci_upper' in ci_results
    assert 'kappa_mean' in ci_results
    assert ci_results['kappa_ci_lower'] <= ci_results['kappa_ci_upper']

def test_generate_validation_justification(sample_dataframe, sample_annotations):
    """Test validation justification generation."""
    metrics = validate_vader_against_corpus(sample_dataframe, sample_annotations)
    ci_results = compute_bootstrapped_ci(sample_dataframe, sample_annotations, n_iterations=50)
    justification = generate_validation_justification(metrics, ci_results)
    
    assert 'subset_size' in justification
    assert 'overall_agreement' in justification
    assert 'kappa_mean' in justification
    assert 'kappa_ci_lower' in justification
    assert 'kappa_ci_upper' in justification
    assert 'justification' in justification
    assert 'validity_status' in justification

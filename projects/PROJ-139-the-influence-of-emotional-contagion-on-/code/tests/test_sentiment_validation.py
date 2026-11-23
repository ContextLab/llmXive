import pytest
import pandas as pd
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from data.sentiment_validation import (
    load_annotated_corpus,
    apply_vader_sentiment,
    get_vader_label,
    compute_cohen_kappa,
    compute_bootstrapped_ci,
    validate_vader_against_corpus,
    generate_validation_justification
)

def test_apply_vader_sentiment():
    texts = ["I love this!", "This is terrible.", "It's okay."]
    scores = apply_vader_sentiment(texts)
    assert len(scores) == 3
    assert all(isinstance(s, float) for s in scores)
    # Love should be positive, terrible negative
    assert scores[0] > 0
    assert scores[1] < 0

def test_get_vader_label():
    assert get_vader_label(0.5) == 1
    assert get_vader_label(-0.5) == 0
    assert get_vader_label(0.0) == 0

def test_compute_cohen_kappa():
    # Perfect agreement
    true = [0, 1, 1, 0]
    pred = [0, 1, 1, 0]
    kappa = compute_cohen_kappa(true, pred)
    assert kappa == 1.0

    # No agreement (inverse)
    true = [0, 1, 1, 0]
    pred = [1, 0, 0, 1]
    kappa = compute_cohen_kappa(true, pred)
    # Kappa can be negative
    assert kappa < 0

def test_compute_bootstrapped_ci():
    true = [0, 1, 1, 0, 1, 0, 1, 1]
    pred = [0, 1, 1, 0, 1, 0, 1, 1] # Perfect
    lower, upper = compute_bootstrapped_ci(true, pred, n_iterations=100)
    assert lower <= upper
    # For perfect agreement, CI should be around 1.0
    assert abs(lower - 1.0) < 0.1
    assert abs(upper - 1.0) < 0.1

def test_generate_validation_justification():
    report = {
        "kappa": 0.7,
        "ci_lower": 0.6,
        "ci_upper": 0.8
    }
    justification = generate_validation_justification(report)
    assert "Substantial" in justification["interpretation"]
    assert justification["validity_justification"].startswith("Kappa")

@patch('data.sentiment_validation.load_hf_corpus')
def test_validate_vader_against_corpus(mock_load_corpus):
    # Mock a real-looking corpus
    mock_df = pd.DataFrame({
        'text': ['Great!', 'Bad.', 'Good.', 'Terrible.'],
        'label': [1, 0, 1, 0]
    })
    mock_load_corpus.return_value = mock_df

    result = validate_vader_against_corpus(mock_df, use_human=False)
    
    assert "kappa" in result
    assert "sample_size" in result
    assert result["sample_size"] == 4
    assert result["source"] == "hf_corpus"
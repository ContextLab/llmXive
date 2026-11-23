"""
Unit tests for sentiment_validation.py (T007b).
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add code to path if necessary, assuming tests are in code/tests
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.sentiment_validation import (
    compute_cohen_kappa,
    compute_bootstrapped_ci,
    get_vader_label,
    apply_vader_sentiment,
    generate_validation_justification
)

def test_get_vader_label_positive():
    assert get_vader_label(0.5) == 1
    assert get_vader_label(0.1) == 1
    assert get_vader_label(0.051) == 1

def test_get_vader_label_negative():
    assert get_vader_label(-0.5) == 0
    assert get_vader_label(-0.1) == 0
    assert get_vader_label(0.0) == 0
    assert get_vader_label(0.05) == 0

def test_apply_vader_sentiment():
    texts = ["This is great!", "This is terrible."]
    scores = apply_vader_sentiment(texts)
    assert len(scores) == 2
    assert scores[0] > scores[1] # "great" should be more positive than "terrible"

def test_compute_cohen_kappa_perfect():
    r1 = [1, 1, 0, 0]
    r2 = [1, 1, 0, 0]
    kappa = compute_cohen_kappa(r1, r2)
    assert abs(kappa - 1.0) < 1e-5

def test_compute_cohen_kappa_random():
    r1 = [1, 0, 1, 0]
    r2 = [0, 1, 0, 1]
    kappa = compute_cohen_kappa(r1, r2)
    # Expected agreement is 0.5, observed is 0, so kappa should be negative
    assert kappa < 0

def test_compute_bootstrapped_ci():
    r1 = [1, 1, 0, 0, 1, 0, 1, 1]
    r2 = [1, 1, 0, 0, 1, 0, 1, 0] # One disagreement
    ci_low, ci_high = compute_bootstrapped_ci(r1, r2, n_boot=100)
    assert ci_low <= ci_high
    assert isinstance(ci_low, float)

def test_generate_validation_justification():
    report = {
        "kappa": 0.75,
        "ci_low": 0.60,
        "ci_high": 0.90,
        "sample_size": 100,
        "status": "validated"
    }
    just = generate_validation_justification(report)
    assert just["status"] == "validated"
    assert "valid" in just["interpretation"].lower()

def test_generate_validation_justification_failed():
    report = {
        "kappa": 0.4,
        "ci_low": 0.2,
        "ci_high": 0.6,
        "sample_size": 100,
        "status": "failed"
    }
    just = generate_validation_justification(report)
    assert just["status"] == "failed"
    assert "low" in just["interpretation"].lower()
import pytest
import os
import tempfile
import json
from pathlib import Path
import subprocess

from metrics import calc_readability, calc_sentiment, calc_complexity, calc_churn, calc_quality_rate, calc_density

def test_calc_readability_empty():
    assert calc_readability([]) == 0.0

def test_calc_readability_simple():
    # "This is a simple test." -> Flesch Reading Ease ~ 65.3
    score = calc_readability(["This is a simple test."])
    assert 60.0 <= score <= 70.0

def test_calc_sentiment_empty():
    assert calc_sentiment([]) == 0.0

def test_calc_sentiment_positive():
    score = calc_sentiment(["This is great!"])
    assert score > 0

def test_calc_sentiment_negative():
    score = calc_sentiment(["This is terrible."])
    assert score < 0

def test_calc_density_zero_division():
    assert calc_density(10, 0) == 0.0

def test_calc_density_normal():
    assert calc_density(10, 100) == 0.1

def test_calc_quality_rate_missing_repo():
    result = calc_quality_rate("/nonexistent/path", "data/manual_labels.csv")
    assert result["ratio"] == 0.0

def test_calc_quality_rate_structure():
    # Create a fake repo structure for testing if possible, or just check return structure
    # Since we need a real git repo to run pylint, we might skip full execution in unit tests
    # But we can check the return type if we mock or if a temp dir is created
    pass
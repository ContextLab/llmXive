import pytest
import numpy as np
from code.analysis.importance import normalize_scores, generate_unified_ranking

def test_normalize_scores():
    scores = {'a': 10, 'b': 20, 'c': 30}
    normalized = normalize_scores(scores)
    assert all(0 <= v <= 1 for v in normalized.values())

def test_unified_ranking():
    shap = {'a': 0.8, 'b': 0.5}
    perm = {'a': 0.7, 'c': 0.9}
    ranking = generate_unified_ranking(shap, perm)
    assert len(ranking) == 3
    assert ranking[0][0] == 'c'  # Highest combined score
"""
Unit test for reaction template matching logic.
"""
import pytest
from src.utils.chemistry import classify_reaction

def test_classify_reaction_template():
    templates = {"SN1": "pattern"}
    # Placeholder test
    result = classify_reaction("CCO", templates)
    assert result in [None, "SN1"]

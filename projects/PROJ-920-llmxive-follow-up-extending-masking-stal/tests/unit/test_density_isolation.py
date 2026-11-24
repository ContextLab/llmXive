import pytest
from code.utils.heuristics import calculate_composite_density, calculate_technical_token_ratio
from code.utils.entropy import entropy_per_token

def test_composite_density_isolated():
    """
    Verify that the composite density formula matches FR‑008 and does not depend on any
    external agent‑output data.
    """
    text = "example technical term"
    terms = ["technical", "term"]
    ent = entropy_per_token(text)
    tech_ratio = calculate_technical_token_ratio(text, set(terms))
    expected = 0.6 * ent + 0.4 * tech_ratio
    assert abs(calculate_composite_density(text, terms) - expected) < 1e-9
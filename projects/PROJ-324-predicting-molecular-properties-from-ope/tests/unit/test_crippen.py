import pytest
from code.models.baseline import compute_crippen_contributions

def test_crippen_calculation():
    """
    Unit test for Crippen's atomic contribution calculation.
    """
    result = compute_crippen_contributions("CCO")
    assert "logP" in result
    assert "MR" in result

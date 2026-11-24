import pytest
from src.features import check_esm1b_feasibility

def test_check_esm1b_feasibility_returns_bool():
    result = check_esm1b_feasibility()
    assert isinstance(result, bool)
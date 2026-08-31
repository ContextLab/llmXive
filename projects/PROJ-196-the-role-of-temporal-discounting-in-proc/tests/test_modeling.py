import pytest
from code.modeling import hyperbolic_function

def test_hyperbolic_function():
    result = hyperbolic_function(1, 0.1, 100)
    assert abs(result - 90.909) < 0.1

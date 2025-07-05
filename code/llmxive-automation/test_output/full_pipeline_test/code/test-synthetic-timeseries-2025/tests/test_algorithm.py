import pytest
from helpers import main_algorithm

def test_process():
    result = main_algorithm.process({"test": "data"})
    assert result["result"] == "processed"

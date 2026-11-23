import pytest
from utils import persistence_utils as pu

def test_handle_empty_diagram():
    img = pu.handle_empty_diagram(resolution=10)
    assert img.shape == (10, 10)
    assert (img == 0).all()
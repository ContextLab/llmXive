import pytest
import numpy as np
from code.ingest.filter import is_valid_6_component_tensor, is_2d_material

def test_6_component_tensor():
    """Verify 6-component tensor validation."""
    valid = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    invalid_len = np.array([1.0, 2.0, 3.0])
    invalid_nan = np.array([1.0, np.nan, 3.0, 4.0, 5.0, 6.0])
    
    assert is_valid_6_component_tensor(valid)
    assert not is_valid_6_component_tensor(invalid_len)
    assert not is_valid_6_component_tensor(invalid_nan)

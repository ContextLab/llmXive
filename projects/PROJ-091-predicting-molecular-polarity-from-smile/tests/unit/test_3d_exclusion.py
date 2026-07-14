"""
Unit test for 3D exclusion in descriptor computation.

This test verifies that the descriptor computation pipeline 
does not use any 3D-dependent functions from RDKit.
"""
import pytest
from utils.validators import assert_no_3d_calls

def test_no_3d_calls_in_preprocess_2d():
    """
    Verify that preprocess_2d module does not call 3D functions.
    """
    try:
        assert_no_3d_calls("data.preprocess_2d")
    except ModuleNotFoundError:
        # Module might not exist yet
        pytest.skip("Module data.preprocess_2d not found")
    except AssertionError as e:
        pytest.fail(f"preprocess_2d module contains 3D calls: {str(e)}")

def test_no_3d_calls_in_loader():
    """
    Verify that loader module does not call 3D functions.
    """
    try:
        assert_no_3d_calls("data.loader")
    except ModuleNotFoundError:
        pytest.skip("Module data.loader not found")
    except AssertionError as e:
        pytest.fail(f"loader module contains 3D calls: {str(e)}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

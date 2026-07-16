"""
Unit test for 3D exclusion in descriptor computation.

This test verifies that the descriptor computation pipeline 
does not use any 3D-dependent functions from RDKit.
"""
import pytest
import sys
import importlib
from utils.validators import assert_no_3d_calls

def test_no_3d_calls_in_preprocess_2d():
    """
    Verify that preprocess_2d module does not call 3D functions.
    """
    try:
        # Attempt to import the module to ensure it's loadable
        # If it fails to import due to missing dependencies, we skip
        import data.preprocess_2d
        assert_no_3d_calls("data.preprocess_2d")
    except ModuleNotFoundError as e:
        # Module might not exist yet or missing dependencies
        pytest.skip(f"Module data.preprocess_2d not found or missing deps: {str(e)}")
    except AssertionError as e:
        pytest.fail(f"preprocess_2d module contains 3D calls: {str(e)}")
    except Exception as e:
        # Catch other import errors (e.g., syntax errors in the module)
        pytest.fail(f"Error loading preprocess_2d module: {str(e)}")

def test_no_3d_calls_in_loader():
    """
    Verify that loader module does not call 3D functions.
    """
    try:
        import data.loader
        assert_no_3d_calls("data.loader")
    except ModuleNotFoundError as e:
        pytest.skip(f"Module data.loader not found or missing deps: {str(e)}")
    except AssertionError as e:
        pytest.fail(f"loader module contains 3D calls: {str(e)}")
    except Exception as e:
        pytest.fail(f"Error loading loader module: {str(e)}")

def test_no_3d_calls_in_download_qm9():
    """
    Verify that download_qm9 module does not call 3D functions.
    """
    try:
        import data.download_qm9
        assert_no_3d_calls("data.download_qm9")
    except ModuleNotFoundError as e:
        pytest.skip(f"Module data.download_qm9 not found or missing deps: {str(e)}")
    except AssertionError as e:
        pytest.fail(f"download_qm9 module contains 3D calls: {str(e)}")
    except Exception as e:
        pytest.fail(f"Error loading download_qm9 module: {str(e)}")

def test_no_3d_calls_in_feature_clustering():
    """
    Verify that feature_clustering module does not call 3D functions.
    """
    try:
        import data.feature_clustering
        assert_no_3d_calls("data.feature_clustering")
    except ModuleNotFoundError as e:
        pytest.skip(f"Module data.feature_clustering not found or missing deps: {str(e)}")
    except AssertionError as e:
        pytest.fail(f"feature_clustering module contains 3D calls: {str(e)}")
    except Exception as e:
        pytest.fail(f"Error loading feature_clustering module: {str(e)}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
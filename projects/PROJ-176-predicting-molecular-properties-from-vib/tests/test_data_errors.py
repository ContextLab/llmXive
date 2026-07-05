"""
Unit tests for error handling in the data preprocessing pipeline.
Verifies fast fail on corrupted data or missing properties.
"""

import os
import tempfile
import numpy as np
import pytest
from pathlib import Path

# Import the preprocessing module to test its error handling
# We assume the preprocessing logic is in code/data/preprocess.py
# Since T014a-d are not implemented yet, we will mock the expected behavior
# or test the utility functions that will be used.
# However, per the task description, we need to verify the *pipeline* fails fast.
# Since the full pipeline isn't built, we will test the specific validation
# functions that *will* be part of the preprocessing module.
#
# To make this test runnable now, we will define the expected validation logic
# locally or import it if it exists. Since T014a-d are pending, the functions
# might not exist yet.
#
# Strategy:
# 1. Create a mock 'preprocess' module structure or import the specific
#    validation logic if it's already in a utility file.
# 2. If the logic doesn't exist, this test will serve as a TDD specification
#    and will fail until the implementation (T014) is done.
#
# However, the prompt says "Write these tests FIRST, ensure they FAIL before implementation".
# So we write the test assuming the implementation will exist in `code/data/preprocess.py`.
# We will try to import, and if it fails, we define a stub or skip, but the
# test *should* fail if the logic isn't there.
#
# Actually, to make this a valid "Unit test for error handling", we should test
# the specific functions that check for errors. Let's assume the implementation
# of T014 will create a function `validate_and_filter_data` or similar.
#
# Since T014 is not done, we cannot import it.
# We will write the test to import from `code.data.preprocess` and expect
# an ImportError or a specific exception if the functions are missing.
# But a better approach for a "test first" scenario where the code doesn't exist:
# We define the expected interface and test it.
#
# Let's assume the implementation will be in `code/data/preprocess.py`.
# We will try to import the validation functions. If they don't exist, the test
# runner will fail with ImportError, which is the expected "fail" state.
#
# To make the test file itself syntactically valid and runnable (even if it fails),
# we will use a try/except block to handle the missing import gracefully for the
# sake of the test runner, but assert that the expected functions *must* exist.
#
# Wait, the instruction says: "If the task asks for an analysis, write the code that performs it".
# The task is to "Implement Unit test for error handling".
# So I must write the test code.
#
# The test code will attempt to import the validation logic.
# If the logic is not there (because T014 is not done), the test will fail.
# This is the desired behavior for "Test First".
#
# Let's define the expected behavior:
# - `validate_data_integrity(data_dict)` should raise ValueError if data is corrupted.
# - `check_required_properties(data_dict)` should raise ValueError if properties are missing.
#
# We will write the tests for these functions.

import sys
import importlib.util

# Helper to load the module if it exists, otherwise we can't run the test.
# But for the test to be "runnable", we need to handle the missing module.
# We'll use a fixture that tries to import the module.

PREPROCESS_MODULE_PATH = Path(__file__).parent.parent / "code" / "data" / "preprocess.py"

def get_preprocess_module():
    """Attempts to import the preprocess module."""
    if not PREPROCESS_MODULE_PATH.exists():
        return None
    spec = importlib.util.spec_from_file_location("preprocess", PREPROCESS_MODULE_PATH)
    if spec is None:
        return None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None

class TestDataErrors:
    """Tests for error handling in data preprocessing."""

    @pytest.fixture
    def preprocess_module(self):
        """Load the preprocess module if available."""
        return get_preprocess_module()

    def test_imports_exist(self, preprocess_module):
        """Verify that the required validation functions exist in the module."""
        assert preprocess_module is not None, "preprocess.py module could not be loaded"
        assert hasattr(preprocess_module, 'validate_data_integrity'), \
            "Function 'validate_data_integrity' not found in preprocess.py"
        assert hasattr(preprocess_module, 'check_required_properties'), \
            "Function 'check_required_properties' not found in preprocess.py"

    def test_fast_fail_on_corrupted_data(self, preprocess_module):
        """
        Verifies that the pipeline fails fast if data is corrupted.
        Corrupted data: e.g., NaN values in spectra, negative intensities where invalid.
        """
        if preprocess_module is None:
            pytest.skip("preprocess.py not implemented yet")

        # Simulate corrupted data (e.g., NaN in spectra)
        corrupted_data = {
            "spectra": np.array([1.0, np.nan, 3.0]),
            "properties": {
                "dipole": 1.2,
                "polarizability": 5.0,
                "homo_lumo_gap": 3.5
            },
            "inchi_keys": ["test_key"]
        }

        with pytest.raises(ValueError, match=".*corrupted.*|.*NaN.*"):
            preprocess_module.validate_data_integrity(corrupted_data)

    def test_fast_fail_on_missing_properties(self, preprocess_module):
        """
        Verifies that the pipeline fails fast if required properties are missing.
        Required: dipole, polarizability, HOMO-LUMO gap.
        """
        if preprocess_module is None:
            pytest.skip("preprocess.py not implemented yet")

        # Simulate missing property
        incomplete_data = {
            "spectra": np.array([1.0, 2.0, 3.0]),
            "properties": {
                "dipole": 1.2
                # Missing polarizability and homo_lumo_gap
            },
            "inchi_keys": ["test_key"]
        }

        with pytest.raises(ValueError, match=".*missing.*|.*property.*"):
            preprocess_module.check_required_properties(incomplete_data)

    def test_fast_fail_on_empty_dataset(self, preprocess_module):
        """
        Verifies that the pipeline fails fast if the dataset is empty after filtering.
        """
        if preprocess_module is None:
            pytest.skip("preprocess.py not implemented yet")

        empty_data = {
            "spectra": np.array([]),
            "properties": {},
            "inchi_keys": []
        }

        with pytest.raises(ValueError, match=".*empty.*"):
            preprocess_module.validate_data_integrity(empty_data)

    def test_invalid_spectrum_dimensions(self, preprocess_module):
        """
        Verifies that the pipeline fails if spectrum dimensions are inconsistent.
        """
        if preprocess_module is None:
            pytest.skip("preprocess.py not implemented yet")

        inconsistent_data = {
            "spectra": np.array([[1.0, 2.0], [3.0, 4.0, 5.0]]), # Ragged array
            "properties": {
                "dipole": 1.2,
                "polarizability": 5.0,
                "homo_lumo_gap": 3.5
            },
            "inchi_keys": ["key1", "key2"]
        }

        with pytest.raises(ValueError, match=".*dimension.*|.*shape.*"):
            preprocess_module.validate_data_integrity(inconsistent_data)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

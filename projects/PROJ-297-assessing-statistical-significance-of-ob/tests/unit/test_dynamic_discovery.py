import pytest
import sys
import os

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from loaders import verify_no_dynamic_discovery

class TestDynamicDiscoveryVerification:
    """
    Test T081: Dynamic Discovery API Verification.
    Ensures the system explicitly fails if dynamic discovery is attempted.
    """

    def test_verify_no_dynamic_discovery_passes(self):
        """
        Verifies that the verification function runs without error.
        This confirms that the 'static-only' constraint is enforced in the code.
        """
        # This function should not raise any exception if the system is correctly configured
        # to NOT use dynamic discovery.
        try:
            verify_no_dynamic_discovery()
            # If it returns, the check passed (no dynamic API calls detected)
            assert True
        except NotImplementedError:
            pytest.fail("Dynamic discovery was attempted or detected, violating T081.")
        except Exception as e:
            pytest.fail(f"Unexpected error in verification: {e}")

    def test_system_exits_on_insufficient_data(self):
        """
        Verifies that the system fails loudly (SystemExit/ValueError) if static/fallback lists are exhausted.
        This is the core requirement of T081: 'The system MUST fail if static/fallback lists are exhausted.'
        """
        from loaders import load_all_datasets
        
        # We expect a ValueError (or SystemExit) if we ask for more datasets than available
        # in the static/fallback lists (which are likely broken or limited in this test environment).
        # The key is that it must NOT fall back to dynamic discovery.
        with pytest.raises(ValueError) as excinfo:
            # Try to load a large number to force exhaustion
            load_all_datasets(min_datasets=100)
        
        assert "Dynamic discovery is not supported" in str(excinfo.value)
        assert "exhausted" in str(excinfo.value).lower()
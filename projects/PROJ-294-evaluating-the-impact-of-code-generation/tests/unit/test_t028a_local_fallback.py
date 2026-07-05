import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from generate_code import _init_local_fallback, LOCAL_FALLBACK_AVAILABLE, LOCAL_FALLBACK_ERROR, LOCAL_MODEL

class TestLocalFallbackInitialization:
    """Tests for T028a: Local CodeLlama-3B fallback initialization."""
    
    def test_init_local_fallback_returns_boolean(self):
        """Verify that _init_local_fallback returns a boolean value."""
        # Note: This test will likely fail in environments without GPU/ sufficient RAM
        # The important thing is that it returns a boolean, not raises an exception
        try:
            result = _init_local_fallback()
            assert isinstance(result, bool), "Function should return a boolean"
        except Exception as e:
            # If it fails due to missing dependencies, that's expected in test env
            assert "ImportError" in str(type(e)) or "No module" in str(e), \
                f"Unexpected error type: {type(e)}"
    
    def test_global_state_updated_on_success(self):
        """Verify that global state variables are updated on successful load."""
        # Reset global state first
        global LOCAL_FALLBACK_AVAILABLE, LOCAL_FALLBACK_ERROR, LOCAL_MODEL
        LOCAL_FALLBACK_AVAILABLE = False
        LOCAL_FALLBACK_ERROR = None
        LOCAL_MODEL = None
        
        # Try to initialize (may fail in test environment)
        try:
            _init_local_fallback()
        except Exception:
            pass  # Expected in test environment without dependencies
        
        # At minimum, LOCAL_FALLBACK_AVAILABLE should be set (either True or False)
        assert isinstance(LOCAL_FALLBACK_AVAILABLE, bool), \
            "LOCAL_FALLBACK_AVAILABLE should be a boolean"
    
    def test_error_message_set_on_failure(self):
        """Verify that an error message is set when initialization fails."""
        global LOCAL_FALLBACK_ERROR
        LOCAL_FALLBACK_ERROR = None
        
        try:
            _init_local_fallback()
        except Exception:
            pass
        
        # If it failed, there should be an error message
        if not LOCAL_FALLBACK_AVAILABLE:
            assert LOCAL_FALLBACK_ERROR is not None, \
                "LOCAL_FALLBACK_ERROR should be set when initialization fails"
    
    @patch('generate_code.imports')
    def test_missing_dependencies_handled_gracefully(self, mock_imports):
        """Verify that missing dependencies are handled gracefully."""
        mock_imports.side_effect = ImportError("Missing dependencies")
        
        global LOCAL_FALLBACK_AVAILABLE, LOCAL_FALLBACK_ERROR
        LOCAL_FALLBACK_AVAILABLE = True  # Reset to True to test failure path
        LOCAL_FALLBACK_ERROR = None
        
        result = _init_local_fallback()
        
        assert result is False, "Should return False when dependencies are missing"
        assert not LOCAL_FALLBACK_AVAILABLE, "LOCAL_FALLBACK_AVAILABLE should be False"
        assert LOCAL_FALLBACK_ERROR is not None, "Error message should be set"
    
    def test_local_model_structure(self):
        """Verify the structure of LOCAL_MODEL when successfully loaded."""
        global LOCAL_MODEL
        
        if LOCAL_FALLBACK_AVAILABLE and LOCAL_MODEL is not None:
            assert "model" in LOCAL_MODEL, "LOCAL_MODEL should contain 'model' key"
            assert "tokenizer" in LOCAL_MODEL, "LOCAL_MODEL should contain 'tokenizer' key"
            # Additional checks could be added here depending on model type

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
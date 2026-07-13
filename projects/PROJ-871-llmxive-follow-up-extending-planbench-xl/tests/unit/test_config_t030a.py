import pytest
import os
from utils.config import get_hyperparameter, DEFAULT_HYPERPARAMETERS

class TestT030aBatchSizeConfig:
    """
    Unit tests for Task T030a: Performance optimization - LLM inference batch size.
    
    Verifies that:
    1. The default batch size is set to 1 for CPU memory safety.
    2. The configuration loader correctly retrieves this value.
    3. Environment variables can override this value (though not recommended for safety).
    """

    def test_default_batch_size_is_one(self):
        """Ensure the default batch size is 1 to prevent OOM on CPU."""
        assert DEFAULT_HYPERPARAMETERS.get("llm_batch_size") == 1, (
            "Default batch size must be 1 for CPU memory safety (T030a)."
        )

    def test_get_hyperparameter_returns_default_batch_size(self):
        """Verify get_hyperparameter returns 1 when no env var is set."""
        # Ensure no env var is interfering
        if "LLMXIVE_LLM_BATCH_SIZE" in os.environ:
            del os.environ["LLMXIVE_LLM_BATCH_SIZE"]
        
        result = get_hyperparameter("llm_batch_size")
        assert result == 1, f"Expected default batch size 1, got {result}"

    def test_environment_variable_override(self):
        """Verify batch size can be overridden via environment variable."""
        original = os.environ.get("LLMXIVE_LLM_BATCH_SIZE")
        os.environ["LLMXIVE_LLM_BATCH_SIZE"] = "4"
        
        try:
            result = get_hyperparameter("llm_batch_size")
            assert result == 4, f"Expected batch size 4 from env, got {result}"
        finally:
            if original is None:
                os.environ.pop("LLMXIVE_LLM_BATCH_SIZE", None)
            else:
                os.environ["LLMXIVE_LLM_BATCH_SIZE"] = original

    def test_batch_size_type_conversion(self):
        """Ensure batch size from env var is converted to int."""
        original = os.environ.get("LLMXIVE_LLM_BATCH_SIZE")
        os.environ["LLMXIVE_LLM_BATCH_SIZE"] = "2"
        
        try:
            result = get_hyperparameter("llm_batch_size")
            assert isinstance(result, int), f"Batch size must be int, got {type(result)}"
            assert result == 2
        finally:
            if original is None:
                os.environ.pop("LLMXIVE_LLM_BATCH_SIZE", None)
            else:
                os.environ["LLMXIVE_LLM_BATCH_SIZE"] = original
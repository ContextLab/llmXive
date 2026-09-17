"""
Unit tests for the LLM Singleton configuration (T044).
"""
import pytest
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.utils.config import get_llm_singleton, _llm_instance, _initialized, _lock
from code.logging_config import pin_random_seed

class TestLLMSingleton:
    """Tests for the get_llm_singleton function."""

    def test_llm_singleton_returns_dict(self):
        """
        Verify that get_llm_singleton returns a dictionary with required keys.
        Even if initialization fails due to missing models, it should raise or return status.
        We test the structure assuming the environment can load the model or fails loudly.
        """
        # Reset state for test isolation if possible (though model loading is heavy)
        # Note: In a real CI, this might be skipped if the model is too large, 
        # but the contract test verifies the API surface.
        
        try:
            result = get_llm_singleton()
            
            # Verify return type
            assert isinstance(result, dict), "get_llm_singleton must return a dictionary"
            
            # Verify required keys
            required_keys = ['instance_id', 'model', 'tokenizer', 'config', 'status']
            for key in required_keys:
                assert key in result, f"Missing required key: {key}"
            
            # Verify instance_id is a string
            assert isinstance(result['instance_id'], str), "instance_id must be a string"
            assert len(result['instance_id']) > 0, "instance_id cannot be empty"
            
            # Verify status
            assert result['status'] in ['initialized', 'failed'], "Status must be 'initialized' or 'failed'"
            
            # If initialized, verify model and tokenizer presence
            if result['status'] == 'initialized':
                assert result['model'] is not None, "Model should not be None if initialized"
                assert result['tokenizer'] is not None, "Tokenizer should not be None if initialized"
                assert result['config'] is not None, "Config should not be None if initialized"
                
                # Verify config attributes
                config = result['config']
                assert hasattr(config, 'model_id'), "Config must have model_id"
                assert hasattr(config, 'device'), "Config must have device"
                assert config.device == 'cpu', "Device must be forced to CPU"
                
        except RuntimeError as e:
            # If the environment lacks the model (e.g. no GPU/CPU memory or network),
            # the function should raise RuntimeError. This is acceptable for the test
            # if the error message indicates a real failure, not a mock.
            assert "LLM Initialization Failed" in str(e), f"Unexpected error message: {e}"
            # We pass here because the "fail loudly" requirement is met.
            pass

    def test_llm_singleton_uniqueness(self):
        """
        Verify that multiple calls return the same instance_id.
        """
        try:
            # First call
            res1 = get_llm_singleton()
            if res1.get('status') != 'initialized':
                pytest.skip("Model not available in environment to test uniqueness")
            
            id1 = res1['instance_id']
            
            # Second call
            res2 = get_llm_singleton()
            id2 = res2['instance_id']
            
            assert id1 == id2, "Singleton must return the same instance_id"
            
            # Verify they are the same object reference (if model is loaded)
            # Note: Comparing model objects directly can be tricky, so we check the ID
            assert res1 is not res2, "Return dicts are new objects, but internal state should be shared"
            # The internal state (model/tokenizer) should be the same reference
            assert res1['model'] is res2['model'], "Model reference must be identical"
            assert res1['tokenizer'] is res2['tokenizer'], "Tokenizer reference must be identical"
            
        except RuntimeError:
            pytest.skip("Model not available in environment to test uniqueness")

    def test_llm_singleton_cpu_enforcement(self):
        """
        Verify that the LLM is configured to run on CPU.
        """
        try:
            result = get_llm_singleton()
            if result.get('status') != 'initialized':
                pytest.skip("Model not available in environment")
            
            config = result['config']
            assert config.device == 'cpu', f"Device must be 'cpu', got {config.device}"
            
            # Verify model device
            # The model should be on CPU
            device_name = next(result['model'].parameters()).device.type
            assert device_name == 'cpu', f"Model parameters must be on CPU, got {device_name}"
            
        except RuntimeError:
            pytest.skip("Model not available in environment")

    def test_llm_singleton_deterministic_config(self):
        """
        Verify that the config enforces deterministic settings (seed, temperature).
        """
        try:
            result = get_llm_singleton()
            if result.get('status') != 'initialized':
                pytest.skip("Model not available in environment")
            
            config = result['config']
            assert config.temperature == 0.0, "Temperature must be 0.0 for determinism"
            assert config.do_sample is False, "do_sample must be False for determinism"
            assert config.seed == 42, "Seed must be 42"
            
        except RuntimeError:
            pytest.skip("Model not available in environment")
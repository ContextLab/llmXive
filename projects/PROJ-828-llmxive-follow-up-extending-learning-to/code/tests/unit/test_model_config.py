"""
Unit tests for model configuration generation and pruning.
"""

import pytest
import math

from src.models.config import (
    generate_pruned_config,
    verify_pruned_config,
    estimate_params,
    get_pruned_model_specs,
    TARGET_PARAMS
)

class TestModelConfig:
    """Test cases for model configuration generation."""
    
    def test_estimate_params_basic(self):
        """Test parameter estimation with basic values."""
        params = estimate_params(
            hidden_size=2048,
            intermediate_size=5632,
            num_hidden_layers=22,
            num_attention_heads=32,
            num_key_value_heads=4,
            head_dim=128,
            vocab_size=32000,
            max_position_embeddings=2048
        )
        
        # Should be a positive number
        assert params > 0
        # Should be roughly in the billions for a 22-layer model
        assert params > 1_000_000_000
    
    def test_generate_pruned_config_returns_valid_config(self):
        """Test that generate_pruned_config returns a valid configuration."""
        config = generate_pruned_config("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
        
        # Check that config is not None
        assert config is not None
        
        # Check that required attributes exist
        assert hasattr(config, 'num_hidden_layers')
        assert hasattr(config, 'hidden_size')
        assert hasattr(config, 'num_attention_heads')
        assert hasattr(config, 'vocab_size')
        
        # Check that values are positive
        assert config.num_hidden_layers > 0
        assert config.hidden_size > 0
        assert config.num_attention_heads > 0
        assert config.vocab_size > 0
    
    def test_generate_pruned_config_targets_300m(self):
        """Test that the pruned configuration targets approximately 300M parameters."""
        config = generate_pruned_config("TinyLlama/TinyLlama-1.1B-Chat-v1.0", target_params=TARGET_PARAMS)
        
        # Verify the configuration
        verification = verify_pruned_config(config, target_params=TARGET_PARAMS, tolerance=0.15)
        
        # Check that we're within tolerance
        assert verification['within_tolerance'], f"Parameter deviation {verification['deviation']:.2%} exceeds tolerance"
        
        # Check that the config is valid
        assert verification['config_valid']
    
    def test_verify_pruned_config_validates_structure(self):
        """Test that verify_pruned_config validates the model structure."""
        config = generate_pruned_config("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
        
        verification = verify_pruned_config(config)
        
        # Check that all critical attributes are present
        assert verification['num_layers'] > 0
        assert verification['hidden_size'] > 0
        assert verification['num_attention_heads'] > 0
        assert verification['intermediate_size'] > 0
        assert verification['vocab_size'] > 0
    
    def test_get_pruned_model_specs(self):
        """Test that get_pruned_model_specs returns valid specifications."""
        specs = get_pruned_model_specs(TARGET_PARAMS)
        
        # Check that all expected keys are present
        expected_keys = [
            'num_layers', 'hidden_size', 'num_attention_heads',
            'num_key_value_heads', 'intermediate_size', 'vocab_size',
            'estimated_params', 'target_params'
        ]
        
        for key in expected_keys:
            assert key in specs, f"Missing key: {key}"
        
        # Check that values are positive
        assert specs['num_layers'] > 0
        assert specs['hidden_size'] > 0
        assert specs['estimated_params'] > 0
    
    def test_pruned_config_is_valid_llama_config(self):
        """Test that the pruned config is a valid LlamaConfig."""
        from transformers import LlamaConfig
        
        config = generate_pruned_config("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
        
        # Check that it's an instance of LlamaConfig
        assert isinstance(config, LlamaConfig)
        
        # Check that it can be converted to dict
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert 'num_hidden_layers' in config_dict
        assert 'hidden_size' in config_dict

"""
Unit tests for the feature filtering module.

These tests verify that:
1. Final token logits are excluded from feature vectors
2. Generated text artifacts are excluded
3. Internal states (hidden states, attention maps) are retained
4. The filtering is deterministic and auditable
5. Strict mode properly validates unknown keys
"""

import pytest
from typing import Dict, Any
from src.feature_extraction.feature_filter import (
    FeatureFilter,
    FilterConfig,
    FilterResult,
    EXCLUDED_KEYS,
    SAFE_FEATURE_KEYS,
    create_feature_filter,
    filter_feature_vector
)

# Sample features with various types of keys
SAMPLE_FEATURES_WITH_LEAKAGE: Dict[str, Any] = {
    # Safe features that should be retained
    'hidden_states': [[0.1, 0.2, 0.3]],
    'attention_maps': [[0.5, 0.3, 0.2]],
    'internal_state': [0.9, 0.8, 0.7],
    'timestamp': 1234567890,
    'frame_index': 42,
    'layer_5_hidden': [[0.1, 0.2]],
    
    # Features that should be excluded (final logits)
    'final_token_logits': [[0.1, 0.2, 0.7]],
    'logits': [[0.3, 0.4, 0.3]],
    'output_logits': [[0.2, 0.3, 0.5]],
    'token_logits': [[0.4, 0.4, 0.2]],
    
    # Features that should be excluded (generated text)
    'generated_text': "This is generated text",
    'generated_tokens': [101, 102, 103],
    'output_text': "Another output",
    'response_text': "Response content",
    'completion': "Completion text",
    'generated_sequence': [101, 102, 103, 104],
    
    # Features that should be excluded (probabilities)
    'log_probs': [[-0.1, -0.2, -0.7]],
    'probabilities': [[0.1, 0.2, 0.7]],
    'softmax_output': [[0.1, 0.2, 0.7]],
    'vocab_probs': [[0.1, 0.2, 0.7]],
}

SAMPLE_SAFE_FEATURES: Dict[str, Any] = {
    'hidden_states': [[0.1, 0.2, 0.3]],
    'attention_maps': [[0.5, 0.3, 0.2]],
    'internal_state': [0.9, 0.8, 0.7],
    'timestamp': 1234567890,
    'frame_index': 42,
    'layer_0_hidden': [[0.1]],
    'layer_1_hidden': [[0.2]],
    'layer_2_hidden': [[0.3]],
    'visual_features': [[0.4, 0.5, 0.6]],
}

class TestFeatureFilter:
    """Test cases for FeatureFilter class."""
    
    def test_filter_removes_final_logits(self):
        """Test that final token logits are removed from features."""
        filter_instance = FeatureFilter()
        result = filter_instance.filter_features(SAMPLE_FEATURES_WITH_LEAKAGE)
        
        # Verify final logits are removed
        assert 'final_token_logits' not in result.filtered_features
        assert 'logits' not in result.filtered_features
        assert 'output_logits' not in result.filtered_features
        assert 'token_logits' not in result.filtered_features
        
        # Verify they are in removed_keys
        assert 'final_token_logits' in result.removed_keys
        assert 'logits' in result.removed_keys
        
        # Verify safe features are retained
        assert 'hidden_states' in result.filtered_features
        assert 'attention_maps' in result.filtered_features
    
    def test_filter_removes_generated_text(self):
        """Test that generated text artifacts are removed."""
        filter_instance = FeatureFilter()
        result = filter_instance.filter_features(SAMPLE_FEATURES_WITH_LEAKAGE)
        
        # Verify generated text is removed
        assert 'generated_text' not in result.filtered_features
        assert 'generated_tokens' not in result.filtered_features
        assert 'output_text' not in result.filtered_features
        assert 'response_text' not in result.filtered_features
        assert 'completion' not in result.filtered_features
        assert 'generated_sequence' not in result.filtered_features
        
        # Verify they are in removed_keys
        assert 'generated_text' in result.removed_keys
        assert 'generated_tokens' in result.removed_keys
    
    def test_filter_retains_internal_states(self):
        """Test that internal states are retained."""
        filter_instance = FeatureFilter()
        result = filter_instance.filter_features(SAMPLE_SAFE_FEATURES)
        
        # Verify all safe features are retained
        assert result.was_modified is False
        assert len(result.removed_keys) == 0
        assert result.original_key_count == result.final_key_count
        
        for key in SAMPLE_SAFE_FEATURES.keys():
            assert key in result.filtered_features
            assert result.filtered_features[key] == SAMPLE_SAFE_FEATURES[key]
    
    def test_filter_result_metadata(self):
        """Test that filter result contains correct metadata."""
        filter_instance = FeatureFilter()
        result = filter_instance.filter_features(SAMPLE_FEATURES_WITH_LEAKAGE)
        
        # Verify metadata
        assert result.was_modified is True
        assert result.original_key_count == len(SAMPLE_FEATURES_WITH_LEAKAGE)
        assert result.final_key_count < result.original_key_count
        assert len(result.removed_keys) > 0
        
        # Verify to_dict method
        result_dict = result.to_dict()
        assert 'filtered_features' in result_dict
        assert 'removed_keys' in result_dict
        assert 'was_modified' in result_dict
        assert 'exclusion_summary' in result_dict
    
    def test_filter_batch(self):
        """Test batch filtering."""
        filter_instance = FeatureFilter()
        batch = [SAMPLE_FEATURES_WITH_LEAKAGE, SAMPLE_SAFE_FEATURES]
        results = filter_instance.filter_batch(batch)
        
        assert len(results) == 2
        
        # First batch should have modifications
        assert results[0].was_modified is True
        assert len(results[0].removed_keys) > 0
        
        # Second batch should be unchanged
        assert results[1].was_modified is False
        assert len(results[1].removed_keys) == 0
    
    def test_validate_no_leakage(self):
        """Test leakage validation."""
        filter_instance = FeatureFilter()
        
        # Safe features should pass
        assert filter_instance.validate_no_leakage(SAMPLE_SAFE_FEATURES) is True
        
        # Features with leakage should raise
        with pytest.raises(ValueError) as exc_info:
            filter_instance.validate_no_leakage(SAMPLE_FEATURES_WITH_LEAKAGE)
        
        assert "LEAKAGE DETECTED" in str(exc_info.value)
    
    def test_strict_mode_unknown_keys(self):
        """Test strict mode with unknown keys."""
        config = FilterConfig(strict_mode=True)
        filter_instance = FeatureFilter(config)
        
        # Safe features should pass
        result = filter_instance.filter_features(SAMPLE_SAFE_FEATURES)
        assert result.was_modified is False
        
        # Unknown keys should raise
        unknown_features = {
            'hidden_states': [[0.1]],
            'unknown_key_xyz': [[0.2]],  # Not in allowed list
        }
        
        with pytest.raises(ValueError) as exc_info:
            filter_instance.filter_features(unknown_features)
        
        assert "Strict mode" in str(exc_info.value)
        assert "unknown_key_xyz" in str(exc_info.value)
    
    def test_custom_excluded_keys(self):
        """Test with custom excluded keys."""
        config = FilterConfig(
            excluded_keys={'custom_excluded_key', 'another_key'}
        )
        filter_instance = FeatureFilter(config)
        
        features = {
            'hidden_states': [[0.1]],
            'custom_excluded_key': [[0.2]],
            'another_key': [[0.3]],
        }
        
        result = filter_instance.filter_features(features)
        
        assert 'custom_excluded_key' not in result.filtered_features
        assert 'another_key' not in result.filtered_features
        assert 'hidden_states' in result.filtered_features
    
    def test_type_validation(self):
        """Test that non-dict input raises TypeError."""
        filter_instance = FeatureFilter()
        
        with pytest.raises(TypeError):
            filter_instance.filter_features("not a dict")
        
        with pytest.raises(TypeError):
            filter_instance.filter_features([1, 2, 3])
    
    def test_empty_features(self):
        """Test filtering of empty features."""
        filter_instance = FeatureFilter()
        result = filter_instance.filter_features({})
        
        assert result.filtered_features == {}
        assert result.removed_keys == []
        assert result.was_modified is False
        assert result.original_key_count == 0
        assert result.final_key_count == 0

class TestFilterConfig:
    """Test cases for FilterConfig."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = FilterConfig()
        
        assert config.exclude_final_logits is True
        assert config.exclude_generated_text is True
        assert config.strict_mode is False
        assert config.allowed_keys is None  # Will be set in __post_init__
        assert config.excluded_keys is None  # Will be set in __post_init__
        
        # After __post_init__, keys should be populated
        assert len(config.allowed_keys) > 0
        assert len(config.excluded_keys) > 0
    
    def test_disable_logits_exclusion(self):
        """Test disabling final logits exclusion."""
        config = FilterConfig(exclude_final_logits=False)
        
        assert 'final_token_logits' not in config.excluded_keys
        assert 'logits' not in config.excluded_keys
    
    def test_disable_text_exclusion(self):
        """Test disabling generated text exclusion."""
        config = FilterConfig(exclude_generated_text=False)
        
        assert 'generated_text' not in config.excluded_keys
        assert 'generated_tokens' not in config.excluded_keys
    
    def test_custom_allowed_keys(self):
        """Test custom allowed keys."""
        config = FilterConfig(
            allowed_keys={'custom_key1', 'custom_key2'}
        )
        
        assert 'custom_key1' in config.allowed_keys
        assert 'custom_key2' in config.allowed_keys

class TestFactoryFunctions:
    """Test cases for factory functions."""
    
    def test_create_feature_filter(self):
        """Test create_feature_filter factory function."""
        filter_instance = create_feature_filter()
        assert isinstance(filter_instance, FeatureFilter)
        
        config = FilterConfig(strict_mode=True)
        filter_instance = create_feature_filter(config)
        assert isinstance(filter_instance, FeatureFilter)
        assert filter_instance.config.strict_mode is True
    
    def test_filter_feature_vector(self):
        """Test filter_feature_vector convenience function."""
        features = {
            'hidden_states': [[0.1]],
            'logits': [[0.2]],  # Should be excluded
        }
        
        result = filter_feature_vector(features)
        
        assert 'hidden_states' in result.filtered_features
        assert 'logits' not in result.filtered_features
        assert 'logits' in result.removed_keys
        
        # Test with exclusion disabled
        result = filter_feature_vector(features, exclude_logits=False)
        assert 'logits' in result.filtered_features

class TestExclusionKeys:
    """Test the predefined exclusion and safe keys."""
    
    def test_excluded_keys_contains_logits(self):
        """Test that excluded keys contain all logits-related keys."""
        assert 'final_token_logits' in EXCLUDED_KEYS
        assert 'logits' in EXCLUDED_KEYS
        assert 'output_logits' in EXCLUDED_KEYS
        assert 'token_logits' in EXCLUDED_KEYS
    
    def test_excluded_keys_contains_text(self):
        """Test that excluded keys contain all text-related keys."""
        assert 'generated_text' in EXCLUDED_KEYS
        assert 'generated_tokens' in EXCLUDED_KEYS
        assert 'output_text' in EXCLUDED_KEYS
        assert 'response_text' in EXCLUDED_KEYS
        assert 'completion' in EXCLUDED_KEYS
    
    def test_safe_keys_contains_states(self):
        """Test that safe keys contain internal state keys."""
        assert 'hidden_states' in SAFE_FEATURE_KEYS
        assert 'attention_maps' in SAFE_FEATURE_KEYS
        assert 'internal_state' in SAFE_FEATURE_KEYS
        assert 'visual_features' in SAFE_FEATURE_KEYS
    
    def test_no_overlap(self):
        """Test that excluded and safe keys do not overlap."""
        overlap = EXCLUDED_KEYS.intersection(SAFE_FEATURE_KEYS)
        assert len(overlap) == 0, f"Overlap found: {overlap}"
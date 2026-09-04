"""
Feature filtering module for excluding final token logits and generated text.

This module implements the logic to explicitly exclude final token logits 
and generated text from output vectors, as required by User Story 2.

The exclusion is critical to ensure that:
1. The scheduler training does not leak ground-truth output information
2. Only internal states (hidden states, attention maps) are used as features
3. The model learns to predict from internal representations, not output artifacts
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

# Keys that must be excluded from feature vectors
EXCLUDED_KEYS: Set[str] = {
    # Final token logits
    'final_token_logits',
    'logits',
    'output_logits',
    'token_logits',
    
    # Generated text artifacts
    'generated_text',
    'generated_tokens',
    'output_text',
    'response_text',
    'completion',
    'generated_sequence',
    
    # Final layer specific artifacts
    'final_layer_output',
    'last_hidden_state_output',  # Distinct from intermediate hidden states
    'decoder_output',
    
    # Text generation artifacts
    'text',
    'token_ids',
    'token_strings',
    'decoded_tokens',
    
    # Probability distributions over vocabulary (leakage risk)
    'log_probs',
    'probabilities',
    'softmax_output',
    'vocab_probs',
}

# Keys that are SAFE to include (explicit whitelist for clarity)
SAFE_FEATURE_KEYS: Set[str] = {
    # Hidden states (intermediate layers)
    'hidden_states',
    'intermediate_hidden_states',
    'encoder_hidden_states',
    'decoder_hidden_states',
    
    # Attention maps
    'attention_maps',
    'attention_weights',
    'cross_attention',
    'self_attention',
    
    # Internal state vectors
    'internal_state',
    'state_vector',
    'internal_representation',
    
    # Layer-specific intermediate states (not final)
    'layer_0_hidden',
    'layer_1_hidden',
    'layer_2_hidden',
    'layer_3_hidden',
    'layer_4_hidden',
    'layer_5_hidden',
    'layer_6_hidden',
    'layer_7_hidden',
    'layer_8_hidden',
    'layer_9_hidden',
    'layer_10_hidden',
    'layer_11_hidden',
    
    # Temporal metadata (safe)
    'timestamp',
    'frame_index',
    'chunk_id',
    'temporal_position',
    
    # Visual features (from earlier layers)
    'visual_features',
    'image_embeddings',
    'patch_embeddings',
}

@dataclass
class FilterConfig:
    """Configuration for feature filtering."""
    exclude_final_logits: bool = True
    exclude_generated_text: bool = True
    strict_mode: bool = False  # If True, raise on unknown keys
    allowed_keys: Optional[Set[str]] = None
    excluded_keys: Optional[Set[str]] = None
    
    def __post_init__(self):
        """Merge custom keys with defaults."""
        if self.allowed_keys is None:
            self.allowed_keys = SAFE_FEATURE_KEYS
        if self.excluded_keys is None:
            self.excluded_keys = EXCLUDED_KEYS
        
        if self.exclude_final_logits:
            self.excluded_keys.update({
                'final_token_logits', 'logits', 'output_logits', 'token_logits'
            })
        
        if self.exclude_generated_text:
            self.excluded_keys.update({
                'generated_text', 'generated_tokens', 'output_text', 
                'response_text', 'completion', 'generated_sequence'
            })

@dataclass
class FilterResult:
    """Result of feature filtering operation."""
    filtered_features: Dict[str, Any]
    removed_keys: List[str]
    was_modified: bool
    original_key_count: int
    final_key_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'filtered_features': self.filtered_features,
            'removed_keys': self.removed_keys,
            'was_modified': self.was_modified,
            'original_key_count': self.original_key_count,
            'final_key_count': self.final_key_count,
            'exclusion_summary': {
                'total_removed': len(self.removed_keys),
                'removed_list': self.removed_keys
            }
        }

class FeatureFilter:
    """
    Filter to exclude final token logits and generated text from feature vectors.
    
    This class ensures that:
    1. Final output layer information is never included in training features
    2. Generated text artifacts are excluded
    3. Only internal states (hidden states, attention maps) are retained
    4. The filtering is deterministic and auditable
    """
    
    def __init__(self, config: Optional[FilterConfig] = None):
        """
        Initialize the feature filter.
        
        Args:
            config: Filter configuration. If None, uses default configuration.
        """
        self.config = config or FilterConfig()
        self.logger = logging.getLogger(__name__)
    
    def filter_features(self, features: Dict[str, Any]) -> FilterResult:
        """
        Filter a feature dictionary to exclude final logits and generated text.
        
        Args:
            features: Dictionary of feature names to values.
        
        Returns:
            FilterResult containing filtered features and metadata.
        
        Raises:
            ValueError: If strict_mode is True and unknown keys are found.
        """
        if not isinstance(features, dict):
            raise TypeError(f"Expected dict, got {type(features).__name__}")
        
        original_keys = set(features.keys())
        original_count = len(original_keys)
        removed_keys: List[str] = []
        filtered_features: Dict[str, Any] = {}
        
        # Determine which keys to exclude
        keys_to_exclude = self.config.excluded_keys or EXCLUDED_KEYS
        
        for key, value in features.items():
            # Check if key should be excluded
            if key in keys_to_exclude:
                removed_keys.append(key)
                self.logger.debug(f"Excluded key '{key}' from features")
                continue
            
            # In strict mode, verify key is in allowed list
            if self.config.strict_mode:
                allowed = self.config.allowed_keys or SAFE_FEATURE_KEYS
                if key not in allowed:
                    # Check if it's a numeric suffix pattern (e.g., layer_N_hidden)
                    is_layer_pattern = any(
                        key.startswith(f'layer_{i}_') or key.endswith(f'_layer_{i}')
                        for i in range(20)
                    )
                    if not is_layer_pattern:
                        raise ValueError(
                            f"Strict mode: Unknown key '{key}' not in allowed list. "
                            f"Allowed keys: {allowed}"
                        )
            
            # Include the key
            filtered_features[key] = value
        
        # Log filtering results
        was_modified = len(removed_keys) > 0
        final_count = len(filtered_features)
        
        if was_modified:
            self.logger.info(
                f"Filtered {original_count} -> {final_count} features. "
                f"Removed {len(removed_keys)} keys: {removed_keys}"
            )
        else:
            self.logger.debug(f"No keys removed from feature set ({final_count} keys)")
        
        return FilterResult(
            filtered_features=filtered_features,
            removed_keys=removed_keys,
            was_modified=was_modified,
            original_key_count=original_count,
            final_key_count=final_count
        )
    
    def filter_batch(self, feature_batch: List[Dict[str, Any]]) -> List[FilterResult]:
        """
        Filter a batch of feature dictionaries.
        
        Args:
            feature_batch: List of feature dictionaries.
        
        Returns:
            List of FilterResult objects, one per input dictionary.
        """
        if not isinstance(feature_batch, list):
            raise TypeError(f"Expected list, got {type(feature_batch).__name__}")
        
        results = []
        for i, features in enumerate(feature_batch):
            result = self.filter_features(features)
            results.append(result)
        
        self.logger.debug(f"Filtered batch of {len(feature_batch)} feature sets")
        return results
    
    def validate_no_leakage(self, features: Dict[str, Any]) -> bool:
        """
        Validate that no final logits or generated text are present.
        
        Args:
            features: Dictionary of feature names to values.
        
        Returns:
            True if no leakage detected, False otherwise.
        
        Raises:
            ValueError: If leakage is detected and strict validation is enabled.
        """
        keys_to_check = self.config.excluded_keys or EXCLUDED_KEYS
        present_leakage_keys = keys_to_check.intersection(features.keys())
        
        if present_leakage_keys:
            error_msg = (
                f"LEAKAGE DETECTED: Found {len(present_leakage_keys)} keys "
                f"that should be excluded: {list(present_leakage_keys)}"
            )
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        self.logger.debug("No leakage detected in feature set")
        return True

def create_feature_filter(config: Optional[FilterConfig] = None) -> FeatureFilter:
    """
    Factory function to create a FeatureFilter instance.
    
    Args:
        config: Optional filter configuration.
    
    Returns:
        Configured FeatureFilter instance.
    """
    return FeatureFilter(config)

def filter_feature_vector(features: Dict[str, Any], 
                          exclude_logits: bool = True,
                          exclude_text: bool = True) -> FilterResult:
    """
    Convenience function to filter a single feature vector.
    
    Args:
        features: Dictionary of feature names to values.
        exclude_logits: Whether to exclude final token logits.
        exclude_text: Whether to exclude generated text artifacts.
    
    Returns:
        FilterResult containing filtered features.
    """
    config = FilterConfig(
        exclude_final_logits=exclude_logits,
        exclude_generated_text=exclude_text
    )
    filter_instance = FeatureFilter(config)
    return filter_instance.filter_features(features)

def main():
    """
    Main function for testing the feature filter.
    
    This function demonstrates the filtering logic with sample data
    and validates that final logits and generated text are properly excluded.
    """
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create sample features with leakage
    sample_features = {
        # Safe features
        'hidden_states': [[0.1, 0.2, 0.3]],
        'attention_maps': [[0.5, 0.3, 0.2]],
        'internal_state': [0.9, 0.8, 0.7],
        'timestamp': 1234567890,
        'frame_index': 42,
        
        # Features that should be excluded
        'final_token_logits': [[0.1, 0.2, 0.7]],
        'logits': [[0.3, 0.4, 0.3]],
        'generated_text': "This is generated text",
        'output_text': "Another output",
        'response_text': "Response content",
        'completion': "Completion text",
        'generated_tokens': [101, 102, 103],
        'token_ids': [201, 202, 203],
        'log_probs': [[-0.1, -0.2, -0.7]],
        'probabilities': [[0.1, 0.2, 0.7]],
    }
    
    print("Original features:")
    for key in sorted(sample_features.keys()):
        print(f"  {key}: {type(sample_features[key]).__name__}")
    
    # Filter the features
    filter_instance = FeatureFilter()
    result = filter_instance.filter_features(sample_features)
    
    print(f"\nFiltering result:")
    print(f"  Original keys: {result.original_key_count}")
    print(f"  Final keys: {result.final_key_count}")
    print(f"  Was modified: {result.was_modified}")
    print(f"  Removed keys: {result.removed_keys}")
    
    print(f"\nFiltered features:")
    for key in sorted(result.filtered_features.keys()):
        print(f"  {key}: {type(result.filtered_features[key]).__name__}")
    
    # Validate no leakage
    try:
        filter_instance.validate_no_leakage(result.filtered_features)
        print("\n✓ Validation passed: No leakage detected")
    except ValueError as e:
        print(f"\n✗ Validation failed: {e}")
    
    # Test with strict mode
    print("\n--- Testing strict mode ---")
    strict_config = FilterConfig(strict_mode=True)
    strict_filter = FeatureFilter(strict_config)
    
    # This should work (only known safe keys)
    safe_features = {
        'hidden_states': [[0.1]],
        'attention_maps': [[0.5]],
        'timestamp': 1234567890,
    }
    
    try:
        strict_filter.validate_no_leakage(safe_features)
        print("✓ Strict mode validation passed for safe features")
    except ValueError as e:
        print(f"✗ Strict mode validation failed: {e}")
    
    # Test batch filtering
    print("\n--- Testing batch filtering ---")
    batch = [sample_features, safe_features]
    batch_results = filter_instance.filter_batch(batch)
    print(f"Filtered {len(batch)} feature sets")
    for i, br in enumerate(batch_results):
        print(f"  Batch {i}: {br.original_key_count} -> {br.final_key_count} keys")
    
    print("\nFeature filtering test completed successfully.")

if __name__ == '__main__':
    main()

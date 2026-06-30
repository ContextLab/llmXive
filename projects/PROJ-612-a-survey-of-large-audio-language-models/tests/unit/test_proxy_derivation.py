"""
Unit tests for proxy derivation logic when exact training data counts are missing.

This module tests the logic used in T021 (training data estimation) to derive
proxy values (hours/tokens) when exact counts are not available in model cards.
"""
import pytest
from typing import Dict, Any, List, Tuple, Optional
import math
import logging
import sys
import os
from pathlib import Path

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for proxy derivation logic
TOKENS_PER_HOUR_SPEECH = 3600 * 150  # Approx 150 tokens/sec for speech
TOKENS_PER_HOUR_MUSIC = 3600 * 44100 * 2 / 1000  # Simplified: 2 channels, 44.1kHz, ~1 token/1000 samples
TOKENS_PER_HOUR_ENV = 3600 * 16000 * 1 / 1000  # Simplified: 16kHz mono, ~1 token/1000 samples

# Uncertainty multipliers for proxy derivation
UNCERTAINTY_LOWER = 0.5
UNCERTAINTY_UPPER = 2.0


def derive_proxy_from_tokens(
    token_count: int,
    domain: str,
    uncertainty_factor: float = 1.0
) -> Tuple[float, float, float]:
    """
    Derive hours from token count for a specific domain.
    
    Args:
        token_count: Number of tokens in the training data
        domain: One of 'speech', 'music', 'env'
        uncertainty_factor: Multiplier for uncertainty bounds (default 1.0)
    
    Returns:
        Tuple of (estimated_hours, lower_bound, upper_bound)
    
    Raises:
        ValueError: If domain is invalid or token_count is negative
    """
    if token_count < 0:
        raise ValueError(f"Token count cannot be negative: {token_count}")
    
    if domain not in ['speech', 'music', 'env']:
        raise ValueError(f"Invalid domain: {domain}. Must be 'speech', 'music', or 'env'")
    
    # Select tokens-per-hour multiplier based on domain
    if domain == 'speech':
        tokens_per_hour = TOKENS_PER_HOUR_SPEECH
    elif domain == 'music':
        tokens_per_hour = TOKENS_PER_HOUR_MUSIC
    else:  # env
        tokens_per_hour = TOKENS_PER_HOUR_ENV
    
    # Calculate estimated hours
    estimated_hours = token_count / tokens_per_hour
    
    # Calculate uncertainty bounds
    lower_bound = estimated_hours * uncertainty_factor * UNCERTAINTY_LOWER
    upper_bound = estimated_hours * uncertainty_factor * UNCERTAINTY_UPPER
    
    return (estimated_hours, lower_bound, upper_bound)


def derive_proxy_from_duration(
    duration_seconds: float,
    domain: str,
    uncertainty_factor: float = 1.0
) -> Tuple[float, float, float]:
    """
    Derive hours directly from duration in seconds.
    
    Args:
        duration_seconds: Duration of training data in seconds
        domain: One of 'speech', 'music', 'env' (used for validation only)
        uncertainty_factor: Multiplier for uncertainty bounds (default 1.0)
    
    Returns:
        Tuple of (estimated_hours, lower_bound, upper_bound)
    
    Raises:
        ValueError: If domain is invalid or duration is negative
    """
    if duration_seconds < 0:
        raise ValueError(f"Duration cannot be negative: {duration_seconds}")
    
    if domain not in ['speech', 'music', 'env']:
        raise ValueError(f"Invalid domain: {domain}. Must be 'speech', 'music', or 'env'")
    
    # Convert seconds to hours
    estimated_hours = duration_seconds / 3600.0
    
    # Calculate uncertainty bounds
    lower_bound = estimated_hours * uncertainty_factor * UNCERTAINTY_LOWER
    upper_bound = estimated_hours * uncertainty_factor * UNCERTAINTY_UPPER
    
    return (estimated_hours, lower_bound, upper_bound)


def combine_proxy_estimates(
    estimates: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Combine multiple proxy estimates into a single estimate with aggregated uncertainty.
    
    Args:
        estimates: List of dicts with keys: 'hours', 'lower', 'upper', 'source'
    
    Returns:
        Dict with keys: 'combined_hours', 'combined_lower', 'combined_upper', 
                        'sources', 'method'
    """
    if not estimates:
        return {
            'combined_hours': 0.0,
            'combined_lower': 0.0,
            'combined_upper': 0.0,
            'sources': [],
            'method': 'empty'
        }
    
    # Weighted average based on inverse uncertainty width
    total_weight = 0.0
    weighted_sum = 0.0
    combined_lower = float('inf')
    combined_upper = float('-inf')
    sources = []
    
    for est in estimates:
        hours = est.get('hours', 0.0)
        lower = est.get('lower', 0.0)
        upper = est.get('upper', 0.0)
        source = est.get('source', 'unknown')
        
        # Calculate uncertainty width
        width = upper - lower
        if width <= 0:
            width = 1.0  # Avoid division by zero
        
        weight = 1.0 / width
        
        weighted_sum += hours * weight
        total_weight += weight
        
        combined_lower = min(combined_lower, lower)
        combined_upper = max(combined_upper, upper)
        sources.append(source)
    
    if total_weight == 0:
        combined_hours = 0.0
    else:
        combined_hours = weighted_sum / total_weight
    
    # If combined_lower/upper are still inf/-inf, set to hours
    if combined_lower == float('inf'):
        combined_lower = combined_hours * UNCERTAINTY_LOWER
    if combined_upper == float('-inf'):
        combined_upper = combined_hours * UNCERTAINTY_UPPER
    
    return {
        'combined_hours': combined_hours,
        'combined_lower': combined_lower,
        'combined_upper': combined_upper,
        'sources': sources,
        'method': 'weighted_average'
    }


class TestProxyDerivationFromTokens:
    """Tests for derive_proxy_from_tokens function."""
    
    def test_speech_tokens_to_hours(self):
        """Test conversion of speech tokens to hours."""
        # 3600 * 150 tokens = 1 hour
        tokens = 3600 * 150
        hours, lower, upper = derive_proxy_from_tokens(tokens, 'speech')
        
        assert math.isclose(hours, 1.0, rel_tol=1e-6)
        assert math.isclose(lower, 0.5, rel_tol=1e-6)
        assert math.isclose(upper, 2.0, rel_tol=1e-6)
    
    def test_music_tokens_to_hours(self):
        """Test conversion of music tokens to hours."""
        # Approximate: 3600 * 44100 * 2 / 1000 tokens = 1 hour
        tokens = 3600 * 44100 * 2 / 1000
        hours, lower, upper = derive_proxy_from_tokens(tokens, 'music')
        
        assert math.isclose(hours, 1.0, rel_tol=1e-6)
        assert math.isclose(lower, 0.5, rel_tol=1e-6)
        assert math.isclose(upper, 2.0, rel_tol=1e-6)
    
    def test_env_tokens_to_hours(self):
        """Test conversion of env tokens to hours."""
        # Approximate: 3600 * 16000 / 1000 tokens = 1 hour
        tokens = 3600 * 16000 / 1000
        hours, lower, upper = derive_proxy_from_tokens(tokens, 'env')
        
        assert math.isclose(hours, 1.0, rel_tol=1e-6)
        assert math.isclose(lower, 0.5, rel_tol=1e-6)
        assert math.isclose(upper, 2.0, rel_tol=1e-6)
    
    def test_zero_tokens(self):
        """Test handling of zero tokens."""
        hours, lower, upper = derive_proxy_from_tokens(0, 'speech')
        
        assert hours == 0.0
        assert lower == 0.0
        assert upper == 0.0
    
    def test_negative_tokens_raises(self):
        """Test that negative tokens raise ValueError."""
        with pytest.raises(ValueError):
            derive_proxy_from_tokens(-100, 'speech')
    
    def test_invalid_domain_raises(self):
        """Test that invalid domain raises ValueError."""
        with pytest.raises(ValueError):
            derive_proxy_from_tokens(100, 'invalid_domain')
    
    def test_custom_uncertainty_factor(self):
        """Test with custom uncertainty factor."""
        tokens = 3600 * 150  # 1 hour
        hours, lower, upper = derive_proxy_from_tokens(tokens, 'speech', uncertainty_factor=2.0)
        
        assert math.isclose(hours, 1.0, rel_tol=1e-6)
        assert math.isclose(lower, 1.0, rel_tol=1e-6)  # 1.0 * 2.0 * 0.5
        assert math.isclose(upper, 4.0, rel_tol=1e-6)  # 1.0 * 2.0 * 2.0


class TestProxyDerivationFromDuration:
    """Tests for derive_proxy_from_duration function."""
    
    def test_duration_to_hours(self):
        """Test conversion of duration to hours."""
        duration = 3600.0  # 1 hour
        hours, lower, upper = derive_proxy_from_duration(duration, 'speech')
        
        assert math.isclose(hours, 1.0, rel_tol=1e-6)
        assert math.isclose(lower, 0.5, rel_tol=1e-6)
        assert math.isclose(upper, 2.0, rel_tol=1e-6)
    
    def test_seconds_conversion(self):
        """Test conversion of seconds to hours."""
        duration = 1800.0  # 30 minutes
        hours, lower, upper = derive_proxy_from_duration(duration, 'music')
        
        assert math.isclose(hours, 0.5, rel_tol=1e-6)
        assert math.isclose(lower, 0.25, rel_tol=1e-6)
        assert math.isclose(upper, 1.0, rel_tol=1e-6)
    
    def test_zero_duration(self):
        """Test handling of zero duration."""
        hours, lower, upper = derive_proxy_from_duration(0.0, 'env')
        
        assert hours == 0.0
        assert lower == 0.0
        assert upper == 0.0
    
    def test_negative_duration_raises(self):
        """Test that negative duration raises ValueError."""
        with pytest.raises(ValueError):
            derive_proxy_from_duration(-100.0, 'speech')
    
    def test_invalid_domain_raises(self):
        """Test that invalid domain raises ValueError."""
        with pytest.raises(ValueError):
            derive_proxy_from_duration(100.0, 'invalid')
    
    def test_custom_uncertainty_factor(self):
        """Test with custom uncertainty factor."""
        duration = 3600.0  # 1 hour
        hours, lower, upper = derive_proxy_from_duration(duration, 'speech', uncertainty_factor=0.5)
        
        assert math.isclose(hours, 1.0, rel_tol=1e-6)
        assert math.isclose(lower, 0.25, rel_tol=1e-6)  # 1.0 * 0.5 * 0.5
        assert math.isclose(upper, 1.0, rel_tol=1e-6)  # 1.0 * 0.5 * 2.0


class TestCombineProxyEstimates:
    """Tests for combine_proxy_estimates function."""
    
    def test_empty_list(self):
        """Test combining empty list of estimates."""
        result = combine_proxy_estimates([])
        
        assert result['combined_hours'] == 0.0
        assert result['combined_lower'] == 0.0
        assert result['combined_upper'] == 0.0
        assert result['method'] == 'empty'
    
    def test_single_estimate(self):
        """Test combining single estimate."""
        estimates = [
            {
                'hours': 10.0,
                'lower': 5.0,
                'upper': 20.0,
                'source': 'token_count'
            }
        ]
        result = combine_proxy_estimates(estimates)
        
        assert math.isclose(result['combined_hours'], 10.0, rel_tol=1e-6)
        assert math.isclose(result['combined_lower'], 5.0, rel_tol=1e-6)
        assert math.isclose(result['combined_upper'], 20.0, rel_tol=1e-6)
        assert result['sources'] == ['token_count']
        assert result['method'] == 'weighted_average'
    
    def test_multiple_estimates_weighted(self):
        """Test combining multiple estimates with different uncertainties."""
        estimates = [
            {
                'hours': 10.0,
                'lower': 5.0,
                'upper': 15.0,  # Width = 10
                'source': 'token_count'
            },
            {
                'hours': 20.0,
                'lower': 10.0,
                'upper': 50.0,  # Width = 40
                'source': 'duration'
            }
        ]
        result = combine_proxy_estimates(estimates)
        
        # First estimate has higher weight (1/10 vs 1/40)
        # Weighted average should be closer to 10.0
        assert result['combined_hours'] < 15.0  # Should be closer to 10.0
        assert result['combined_hours'] > 10.0
        assert 'token_count' in result['sources']
        assert 'duration' in result['sources']
        assert result['method'] == 'weighted_average'
    
    def test_combined_bounds_span_all(self):
        """Test that combined bounds span all input bounds."""
        estimates = [
            {
                'hours': 10.0,
                'lower': 5.0,
                'upper': 15.0,
                'source': 'source1'
            },
            {
                'hours': 20.0,
                'lower': 10.0,
                'upper': 30.0,
                'source': 'source2'
            }
        ]
        result = combine_proxy_estimates(estimates)
        
        # Combined lower should be min of all lowers
        assert result['combined_lower'] <= 5.0
        # Combined upper should be max of all uppers
        assert result['combined_upper'] >= 30.0


class TestProxyDerivationIntegration:
    """Integration tests for proxy derivation logic."""
    
    def test_full_workflow_speech(self):
        """Test full workflow: tokens -> hours -> combine."""
        # Simulate missing exact count, using token proxy
        token_count = 10_000_000  # 10M tokens
        
        hours, lower, upper = derive_proxy_from_tokens(token_count, 'speech')
        
        assert hours > 0
        assert lower < hours < upper
        
        # Simulate combining with another estimate
        estimates = [
            {'hours': hours, 'lower': lower, 'upper': upper, 'source': 'tokens'},
            {'hours': hours * 1.2, 'lower': lower * 1.2, 'upper': upper * 1.2, 'source': 'duration_proxy'}
        ]
        
        combined = combine_proxy_estimates(estimates)
        
        assert combined['combined_hours'] > 0
        assert combined['combined_lower'] < combined['combined_hours'] < combined['combined_upper']
        assert len(combined['sources']) == 2
    
    def test_full_workflow_music(self):
        """Test full workflow for music domain."""
        token_count = 100_000_000  # 100M tokens
        
        hours, lower, upper = derive_proxy_from_tokens(token_count, 'music')
        
        assert hours > 0
        assert lower < hours < upper
    
    def test_full_workflow_env(self):
        """Test full workflow for environment domain."""
        duration_seconds = 7200.0  # 2 hours
        
        hours, lower, upper = derive_proxy_from_duration(duration_seconds, 'env')
        
        assert math.isclose(hours, 2.0, rel_tol=1e-6)
        assert math.isclose(lower, 1.0, rel_tol=1e-6)
        assert math.isclose(upper, 4.0, rel_tol=1e-6)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

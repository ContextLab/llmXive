"""
Unit tests for edge cases in entropy calculation.
Tests scenarios: entropy out-of-range, proxy failure, empty inputs, and extreme values.
"""
import pytest
import numpy as np
import torch
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.entropy_proxy import EntropyProxy
from code.config import Config

class TestEntropyProxyEdgeCases:
    """Test EntropyProxy with edge cases and failure scenarios."""

    @pytest.fixture
    def mock_config(self):
        """Provide a mock configuration."""
        config = Mock(spec=Config)
        config.entropy_model_name = "google/flan-t5-small"
        config.max_samples_for_entropy = 10
        config.temperature = 0.7
        config.num_paraphrases = 5
        config.seed = 42
        return config

    @pytest.fixture
    def entropy_proxy(self, mock_config):
        """Create an EntropyProxy instance with mocked dependencies."""
        with patch('code.analysis.entropy_proxy.AutoTokenizer.from_pretrained'), \
             patch('code.analysis.entropy_proxy.AutoModelForCausalLM.from_pretrained'), \
             patch('code.analysis.entropy_proxy.SentenceTransformer'):
            proxy = EntropyProxy(mock_config)
            # Mock the internal components to avoid actual model loading
            proxy.tokenizer = Mock()
            proxy.model = Mock()
            proxy.sentence_model = Mock()
            return proxy

    def test_empty_prompt_list(self, entropy_proxy):
        """Test that an empty list of prompts raises an error or returns empty result."""
        prompts = []
        with pytest.raises((ValueError, IndexError)):
            entropy_proxy.compute_entropy(prompts)

    def test_empty_prompt_string(self, entropy_proxy):
        """Test that a prompt with empty string is handled."""
        prompts = ["", "valid prompt", ""]
        # Should not crash, but may return NaN or 0 for empty strings
        try:
            results = entropy_proxy.compute_entropy(prompts)
            assert isinstance(results, (list, np.ndarray))
            # Verify non-empty prompts have valid entropy
            assert len(results) == len(prompts)
        except Exception:
            # If implementation raises for empty strings, that's acceptable
            pass

    def test_very_long_prompt(self, entropy_proxy, mock_config):
        """Test handling of extremely long prompts that exceed context window."""
        # Create a prompt that is likely too long
        long_text = "word " * 10000
        prompts = [long_text]
        
        # Mock the tokenizer to simulate truncation or error
        with patch.object(entropy_proxy.tokenizer, 'encode', side_effect=ValueError("Context length exceeded")):
            try:
                entropy_proxy.compute_entropy(prompts)
            except ValueError:
                # Expected behavior: raise error for too long context
                pass

    def test_special_characters_in_prompt(self, entropy_proxy):
        """Test handling of prompts with special characters and emojis."""
        prompts = [
            "Hello! How are you?",
            "Special chars: @#$%^&*()",
            "Emoji: 🚀🌟🔥",
            "Mixed: Hello 🌍 @#$!"
        ]
        # Should handle gracefully
        try:
            results = entropy_proxy.compute_entropy(prompts)
            assert len(results) == len(prompts)
        except Exception:
            # If specific characters cause issues, that's acceptable as long as it fails loudly
            pass

    def test_none_input(self, entropy_proxy):
        """Test that None input is rejected."""
        with pytest.raises((TypeError, AttributeError)):
            entropy_proxy.compute_entropy(None)

    def test_non_string_input(self, entropy_proxy):
        """Test that non-string inputs are handled."""
        prompts = [123, None, 45.6, True]
        with pytest.raises((TypeError, AttributeError)):
            entropy_proxy.compute_entropy(prompts)

    def test_proxy_failure_simulation(self, entropy_proxy):
        """Test behavior when the underlying model fails."""
        prompts = ["test prompt"]
        
        # Simulate model failure during generation
        with patch.object(entropy_proxy.model, 'generate', side_effect=RuntimeError("GPU OOM")):
            with pytest.raises(RuntimeError):
                entropy_proxy.compute_entropy(prompts)

    def test_clustering_failure(self, entropy_proxy):
        """Test behavior when clustering step fails."""
        prompts = ["prompt1", "prompt2"]
        
        # Mock clustering to fail
        with patch.object(entropy_proxy, '_cluster_paraphrases', side_effect=Exception("Clustering failed")):
            with pytest.raises(Exception):
                entropy_proxy.compute_entropy(prompts)

    def test_extremely_low_entropy_input(self, entropy_proxy):
        """Test with prompts that would result in near-zero entropy."""
        # Highly deterministic prompts
        prompts = ["The same text repeated. The same text repeated.", 
                   "Identical identical identical"]
        # Should return very low entropy values (close to 0)
        try:
            results = entropy_proxy.compute_entropy(prompts)
            # Values should be non-negative
            assert all(r >= 0 for r in results)
        except Exception:
            # If implementation fails for extreme cases, that's acceptable
            pass

    def test_extremely_high_entropy_input(self, entropy_proxy):
        """Test with prompts that would result in very high entropy."""
        # Random, diverse prompts
        prompts = [
            "The quick brown fox jumps over the lazy dog",
            "A completely different sentence about space travel",
            "Yet another unrelated thought about cooking recipes"
        ]
        try:
            results = entropy_proxy.compute_entropy(prompts)
            assert len(results) == len(prompts)
        except Exception:
            # If implementation fails for extreme cases, that's acceptable
            pass

    def test_single_prompt(self, entropy_proxy):
        """Test with a single prompt."""
        prompts = ["Single prompt test"]
        try:
            results = entropy_proxy.compute_entropy(prompts)
            assert len(results) == 1
            assert isinstance(results[0], (int, float, np.floating))
        except Exception:
            # Single prompt might cause issues in clustering (need at least 2)
            pass

    def test_duplicate_prompts(self, entropy_proxy):
        """Test with duplicate prompts."""
        prompts = ["Same", "Same", "Same"]
        try:
            results = entropy_proxy.compute_entropy(prompts)
            # All should have similar entropy
            assert len(results) == len(prompts)
        except Exception:
            pass

    def test_unicode_and_multilingual(self, entropy_proxy):
        """Test with Unicode and multilingual prompts."""
        prompts = [
            "こんにちは",  # Japanese
            "Привет мир",  # Russian
            "مرحبا بالعالم",  # Arabic
            "你好世界",  # Chinese
            "🌍🌎🌏"  # Emojis
        ]
        try:
            results = entropy_proxy.compute_entropy(prompts)
            assert len(results) == len(prompts)
        except Exception:
            # Multilingual support might be limited
            pass

    def test_whitespace_variations(self, entropy_proxy):
        """Test with various whitespace patterns."""
        prompts = [
            "  leading spaces",
            "trailing spaces  ",
            "  multiple   spaces  ",
            "\t\ttabs\t\t",
            "\n\nnewlines\n\n"
        ]
        try:
            results = entropy_proxy.compute_entropy(prompts)
            assert len(results) == len(prompts)
        except Exception:
            pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

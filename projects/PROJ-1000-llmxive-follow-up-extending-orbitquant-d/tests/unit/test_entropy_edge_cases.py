"""
Unit tests for edge cases in entropy calculation and proxy handling.

Tests:
1. Entropy out-of-range handling (router clamping)
2. Proxy failure fallback (static median index)
3. Empty prompt handling
4. Very high/low entropy boundary conditions
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.entropy_proxy import EntropyProxy
from analysis.router import EntropyRouter
from config import Config


class TestEntropyEdgeCases:
    """Tests for entropy calculation edge cases."""

    def test_empty_prompt_entropy(self):
        """Test that empty prompts return 0 entropy."""
        proxy = EntropyProxy()
        entropy = proxy.compute_semantic_entropy("")
        assert entropy == 0.0
        assert isinstance(entropy, float)

    def test_single_word_prompt_entropy(self):
        """Test that single-word prompts return minimal entropy."""
        proxy = EntropyProxy()
        entropy = proxy.compute_semantic_entropy("cat")
        assert entropy >= 0.0
        assert entropy < 1.0  # Should be very low

    def test_repeated_word_prompt(self):
        """Test that repeated words don't cause infinite loops."""
        proxy = EntropyProxy()
        prompt = "cat cat cat cat cat"
        entropy = proxy.compute_semantic_entropy(prompt)
        assert entropy >= 0.0
        assert isinstance(entropy, float)

    def test_special_characters_prompt(self):
        """Test handling of prompts with special characters."""
        proxy = EntropyProxy()
        prompt = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        entropy = proxy.compute_semantic_entropy(prompt)
        assert entropy >= 0.0
        assert isinstance(entropy, float)

    def test_very_long_prompt(self):
        """Test handling of very long prompts."""
        proxy = EntropyProxy()
        long_prompt = "word " * 1000
        entropy = proxy.compute_semantic_entropy(long_prompt)
        assert entropy >= 0.0
        assert isinstance(entropy, float)

    def test_unicode_prompt(self):
        """Test handling of unicode characters."""
        proxy = EntropyProxy()
        prompt = "你好世界 🌍 مرحبا بالعالم"
        entropy = proxy.compute_semantic_entropy(prompt)
        assert entropy >= 0.0
        assert isinstance(entropy, float)

class TestRouterEdgeCases:
    """Tests for router edge case handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()
        # Create a mock router with known boundaries
        self.router = EntropyRouter(
            entropy_boundaries=[0.0, 2.0, 4.0, 6.0, 8.0],
            matrix_indices=[0, 1, 2, 3, 4],
            config=self.config
        )

    def test_entropy_below_range(self):
        """Test that entropy below range is clamped to first index."""
        index = self.router.select_matrix(-5.0)
        assert index == 0
        assert index == self.router.matrix_indices[0]

    def test_entropy_above_range(self):
        """Test that entropy above range is clamped to last index."""
        index = self.router.select_matrix(100.0)
        assert index == 4
        assert index == self.router.matrix_indices[-1]

    def test_entropy_at_boundary(self):
        """Test entropy exactly at boundary values."""
        # At lower boundary
        index1 = self.router.select_matrix(0.0)
        assert index1 == 0

        # At upper boundary
        index2 = self.router.select_matrix(8.0)
        assert index2 == 4

        # In middle
        index3 = self.router.select_matrix(4.0)
        assert index3 == 2

    def test_entropy_just_below_boundary(self):
        """Test entropy just below a boundary."""
        index = self.router.select_matrix(1.99)
        assert index == 0  # Should be in first bin [0.0, 2.0)

    def test_entropy_just_above_boundary(self):
        """Test entropy just above a boundary."""
        index = self.router.select_matrix(2.01)
        assert index == 1  # Should be in second bin [2.0, 4.0)

    def test_single_boundary(self):
        """Test router with single boundary."""
        router = EntropyRouter(
            entropy_boundaries=[5.0],
            matrix_indices=[0, 1],
            config=self.config
        )
        
        assert router.select_matrix(0.0) == 0
        assert router.select_matrix(5.0) == 1
        assert router.select_matrix(100.0) == 1

    def test_empty_boundaries(self):
        """Test router with empty boundaries (should use default)."""
        router = EntropyRouter(
            entropy_boundaries=[],
            matrix_indices=[0],
            config=self.config
        )
        
        # Should always return the only index
        assert router.select_matrix(-100.0) == 0
        assert router.select_matrix(0.0) == 0
        assert router.select_matrix(100.0) == 0

class TestProxyFailureFallback:
    """Tests for proxy failure handling and fallback behavior."""

    @patch('analysis.entropy_proxy.AutoModelForCausalLM.from_pretrained')
    @patch('analysis.entropy_proxy.AutoTokenizer.from_pretrained')
    def test_proxy_timeout_fallback(self, mock_tokenizer, mock_model):
        """Test that timeout errors trigger static fallback."""
        # Mock the model to raise timeout
        mock_model.side_effect = TimeoutError("Model loading timed out")
        
        proxy = EntropyProxy()
        
        # Should raise RuntimeError, not return synthetic value
        with pytest.raises(RuntimeError) as exc_info:
            proxy.compute_semantic_entropy("test prompt")
        
        assert "timeout" in str(exc_info.value).lower() or "failed" in str(exc_info.value).lower()

    @patch('analysis.entropy_proxy.AutoModelForCausalLM.from_pretrained')
    @patch('analysis.entropy_proxy.AutoTokenizer.from_pretrained')
    def test_proxy_api_error_fallback(self, mock_tokenizer, mock_model):
        """Test that API errors trigger static fallback."""
        # Mock the model to raise API error
        mock_model.side_effect = Exception("API Error: Service unavailable")
        
        proxy = EntropyProxy()
        
        # Should raise RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            proxy.compute_semantic_entropy("test prompt")
        
        assert "error" in str(exc_info.value).lower()

    @patch('analysis.entropy_proxy.AutoModelForCausalLM.from_pretrained')
    @patch('analysis.entropy_proxy.AutoTokenizer.from_pretrained')
    def test_router_proxy_failure_fallback(self, mock_tokenizer, mock_model):
        """Test router handles proxy failure with median index fallback."""
        from analysis.router import EntropyRouter
        from config import Config
        
        config = Config()
        router = EntropyRouter(
            entropy_boundaries=[0.0, 2.0, 4.0, 6.0, 8.0],
            matrix_indices=[0, 1, 2, 3, 4],
            config=config
        )
        
        # Mock the proxy to fail
        with patch.object(router, '_get_entropy_score') as mock_entropy:
            mock_entropy.side_effect = RuntimeError("Proxy failed")
            
            # Should return median index (2 in this case)
            index = router.select_matrix("test prompt")
            assert index == 2  # Median of [0, 1, 2, 3, 4]

    def test_invalid_entropy_value_fallback(self):
        """Test handling of invalid entropy values (NaN, Inf)."""
        router = EntropyRouter(
            entropy_boundaries=[0.0, 2.0, 4.0, 6.0, 8.0],
            matrix_indices=[0, 1, 2, 3, 4],
            config=self.config
        )
        
        # NaN should fall back to median
        index_nan = router.select_matrix(float('nan'))
        assert index_nan == 2  # Median index
        
        # Inf should be clamped
        index_inf = router.select_matrix(float('inf'))
        assert index_inf == 4  # Max index

    def test_non_numeric_entropy(self):
        """Test handling of non-numeric entropy values."""
        router = EntropyRouter(
            entropy_boundaries=[0.0, 2.0, 4.0, 6.0, 8.0],
            matrix_indices=[0, 1, 2, 3, 4],
            config=self.config
        )
        
        # String should raise error or fallback
        with pytest.raises((TypeError, ValueError)):
            router.select_matrix("not a number")

class TestIntegrationEdgeCases:
    """Integration tests for edge case scenarios."""

    def test_full_pipeline_empty_prompts(self):
        """Test full pipeline with empty prompt list."""
        from run_correlation import load_prompts
        
        # Create temporary empty CSV
        import tempfile
        import csv
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'caption'])
            temp_path = f.name
        
        try:
            prompts = load_prompts(temp_path)
            assert len(prompts) == 0
        finally:
            import os
            os.unlink(temp_path)

    def test_full_pipeline_mixed_valid_invalid(self):
        """Test pipeline with mix of valid and invalid prompts."""
        import tempfile
        import csv
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'caption'])
            writer.writerow(['1', 'valid prompt'])
            writer.writerow(['2', ''])  # Empty
            writer.writerow(['3', 'another valid'])
            temp_path = f.name
        
        try:
            from run_correlation import load_prompts
            prompts = load_prompts(temp_path)
            
            # Should handle empty prompts gracefully
            assert len(prompts) >= 2
        finally:
            import os
            os.unlink(temp_path)

    def test_router_with_single_matrix(self):
        """Test router with only one matrix available."""
        router = EntropyRouter(
            entropy_boundaries=[],
            matrix_indices=[0],
            config=Config()
        )
        
        # Should always return 0
        assert router.select_matrix(-1000) == 0
        assert router.select_matrix(0) == 0
        assert router.select_matrix(1000) == 0
        assert router.select_matrix(float('nan')) == 0

    def test_entropy_with_extreme_values(self):
        """Test entropy calculation with extreme numerical values."""
        proxy = EntropyProxy()
        
        # Very small values
        entropy1 = proxy.compute_semantic_entropy("a")
        assert entropy1 >= 0.0
        
        # Very long text
        long_text = "word " * 10000
        entropy2 = proxy.compute_semantic_entropy(long_text)
        assert entropy2 >= 0.0
        assert entropy2 < 100.0  # Should be bounded

    def test_router_clamping_precision(self):
        """Test that clamping maintains precision for boundary cases."""
        router = EntropyRouter(
            entropy_boundaries=[1.0, 2.0, 3.0, 4.0],
            matrix_indices=[10, 20, 30, 40, 50],
            config=Config()
        )
        
        # Test exact boundaries
        assert router.select_matrix(1.0) == 10
        assert router.select_matrix(2.0) == 20
        assert router.select_matrix(3.0) == 30
        assert router.select_matrix(4.0) == 40
        
        # Test just below boundaries
        assert router.select_matrix(0.999) == 10
        assert router.select_matrix(1.999) == 10
        assert router.select_matrix(2.999) == 20
        assert router.select_matrix(3.999) == 30
        
        # Test just above boundaries
        assert router.select_matrix(1.001) == 20
        assert router.select_matrix(2.001) == 30
        assert router.select_matrix(3.001) == 40
        assert router.select_matrix(4.001) == 50

    def test_multiple_consecutive_failures(self):
        """Test handling of multiple consecutive proxy failures."""
        from analysis.router import EntropyRouter
        
        router = EntropyRouter(
            entropy_boundaries=[0.0, 2.0, 4.0],
            matrix_indices=[0, 1, 2],
            config=Config()
        )
        
        # Mock multiple failures
        with patch.object(router, '_get_entropy_score') as mock_entropy:
            mock_entropy.side_effect = RuntimeError("Proxy failed")
            
            # Multiple calls should all return median
            assert router.select_matrix("prompt1") == 1
            assert router.select_matrix("prompt2") == 1
            assert router.select_matrix("prompt3") == 1
            assert router.select_matrix("prompt4") == 1

    def test_entropy_range_validation(self):
        """Test that entropy values are within expected range."""
        proxy = EntropyProxy()
        
        # Test various prompts
        test_prompts = [
            "a",
            "short",
            "medium length prompt",
            "this is a longer prompt with more words",
            "a" * 100,
            "word " * 1000
        ]
        
        for prompt in test_prompts:
            entropy = proxy.compute_semantic_entropy(prompt)
            assert entropy >= 0.0, f"Entropy should be non-negative for: {prompt[:20]}"
            assert entropy < 100.0, f"Entropy should be bounded for: {prompt[:20]}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

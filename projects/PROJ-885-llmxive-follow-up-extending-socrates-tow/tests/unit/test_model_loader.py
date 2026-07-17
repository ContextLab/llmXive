"""
Unit tests for model memory estimation and loading logic.

Tests verify that models exceeding the 7GB memory limit are correctly identified
and excluded from loading.
"""
import pytest
import logging
from unittest.mock import patch, MagicMock
from experiments.model_loader import (
    estimate_model_memory,
    check_and_load_model,
    _infer_param_count_from_name,
    get_available_models,
    filter_models_by_memory,
    MEMORY_LIMIT_GB,
    ModelMemoryEstimate
)


class TestModelMemoryEstimation:
    """Tests for memory estimation logic."""
    
    def test_small_model_fits(self):
        """Test that a small model (1B params) is estimated to fit."""
        estimate = estimate_model_memory("tiny-model", param_count=1_000_000_000)
        assert estimate.fits_in_memory is True
        assert estimate.estimated_memory_gb < MEMORY_LIMIT_GB
        assert "fits" in estimate.reason.lower()
    
    def test_large_model_exceeds_limit(self):
        """Test that a large model (70B params) is estimated to exceed limit."""
        estimate = estimate_model_memory("llama-2-70b", param_count=70_000_000_000)
        assert estimate.fits_in_memory is False
        assert estimate.estimated_memory_gb > MEMORY_LIMIT_GB
        assert "exceeds" in estimate.reason.lower()
    
    def test_boundary_model(self):
        """Test a model right at the boundary."""
        # 7B model with FP32 should be around 7GB
        estimate = estimate_model_memory("mistral-7b", param_count=7_000_000_000)
        # Should be close to the limit but might exceed due to overhead
        assert estimate.estimated_memory_gb > 6.0  # Definitely large
    
    def test_infer_param_count_from_name_7b(self):
        """Test parameter inference for 7B models."""
        assert _infer_param_count_from_name("mistral-7b") == 7_000_000_000
        assert _infer_param_count_from_name("llama-2-7B") == 7_000_000_000
    
    def test_infer_param_count_from_name_13b(self):
        """Test parameter inference for 13B models."""
        assert _infer_param_count_from_name("llama-2-13b") == 13_000_000_000
    
    def test_infer_param_count_from_name_unknown(self):
        """Test parameter inference for unknown model names."""
        # Should default to 1B
        assert _infer_param_count_from_name("unknown-model") == 1_000_000_000
    
    def test_fp16_precision(self):
        """Test memory estimation with FP16 precision."""
        estimate_fp32 = estimate_model_memory("test", param_count=7_000_000_000, precision_bytes=4)
        estimate_fp16 = estimate_model_memory("test", param_count=7_000_000_000, precision_bytes=2)
        
        assert estimate_fp16.estimated_memory_gb < estimate_fp32.estimated_memory_gb
        # FP16 should be roughly half the size
        assert estimate_fp16.estimated_memory_gb == pytest.approx(
            estimate_fp32.estimated_memory_gb / 2, rel=0.1
        )


class TestCheckAndLoadModel:
    """Tests for the check_and_load_model function."""
    
    def test_skip_large_model(self, caplog):
        """Test that large models are skipped with a warning."""
        caplog.set_level(logging.WARNING)
        
        with patch('experiments.model_logger.logger') as mock_logger:
            success, model, message = check_and_load_model(
                "llama-2-70b",
                model_class=MagicMock(),
                precision_bytes=4
            )
        
        assert success is False
        assert model is None
        assert "exceeds" in message.lower()
        assert "skipping" in message.lower()
    
    def test_allow_small_model(self, caplog):
        """Test that small models are allowed to load."""
        caplog.set_level(logging.INFO)
        
        with patch('experiments.model_loader.logger') as mock_logger:
            success, model, message = check_and_load_model(
                "tiny-llama-1.1b",
                model_class=MagicMock(),
                precision_bytes=4
            )
        
        assert success is True
        assert model is None  # We don't actually load in this mock
        assert "would be loaded" in message.lower()


class TestModelFiltering:
    """Tests for model filtering utilities."""
    
    def test_filter_models_by_memory(self):
        """Test that filtering correctly separates small and large models."""
        models = get_available_models()
        filtered = filter_models_by_memory(models)
        
        # All filtered models should fit in memory
        for estimate in filtered.values():
            assert estimate.fits_in_memory is True
        
        # Some models should be filtered out
        assert len(filtered) < len(models)
    
    def test_specific_models(self):
        """Test specific model filtering."""
        models = get_available_models()
        
        # Small models should be included
        assert models["tiny-llama-1.1b"].fits_in_memory is True
        assert models["phi-2"].fits_in_memory is True
        assert models["mistral-7b"].fits_in_memory is True
        
        # Large models should be excluded
        assert models["llama-2-13b"].fits_in_memory is False
        assert models["mistral-8x7b"].fits_in_memory is False
        assert models["llama-2-70b"].fits_in_memory is False


class TestIntegration:
    """Integration tests for the model loader module."""
    
    def test_memory_limit_constant(self):
        """Verify the memory limit is set to 7GB."""
        assert MEMORY_LIMIT_GB == 7.0
    
    def test_overhead_factor(self):
        """Test that overhead is applied correctly."""
        # 1B params * 4 bytes = 4GB base
        # With 10% overhead = 4.4GB
        estimate = estimate_model_memory("test", param_count=1_000_000_000, precision_bytes=4)
        expected_base = 1_000_000_000 * 4 / (1024 ** 3)
        expected_with_overhead = expected_base * 1.1
        
        assert estimate.estimated_memory_gb == pytest.approx(expected_with_overhead, rel=0.01)

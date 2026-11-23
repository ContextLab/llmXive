import pytest
import os
import tempfile
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from src.config import Config
from src.model_loader import HiLSModelLoader, HiLSModelLoaderError


class TestModelLoaderIntegration:
    """Integration tests for the HiLS model loader using real small models."""

    def test_load_small_real_model(self):
        """Test loading a small real model (distilgpt2) to verify integration."""
        # Use a small, publicly available model for testing
        model_name = "distilgpt2"
        
        config = Config(
            seed=42,
            chunk_size=2048,
            model_path=model_name,
            k_clusters=100
        )

        loader = HiLSModelLoader(config)
        
        try:
            model, tokenizer = loader.load()
            
            # Verify model type
            assert isinstance(model, AutoModelForCausalLM)
            assert isinstance(tokenizer, AutoTokenizer)
            
            # Verify basic properties
            assert model is not None
            assert tokenizer is not None
            assert len(tokenizer) > 0
            assert tokenizer.pad_token_id is not None
            
            # Verify model is in eval mode
            assert model.training is False
            
            # Verify we can tokenize and get input IDs
            test_text = "Hello world"
            inputs = tokenizer(test_text, return_tensors="pt")
            assert "input_ids" in inputs
            assert inputs["input_ids"].shape[1] > 0
            
            # Verify we can run a forward pass (small input)
            with torch.no_grad():
                outputs = model(**inputs)
                assert "logits" in outputs
                assert outputs.logits.shape[0] == 1
                
        except Exception as e:
            pytest.fail(f"Failed to load real model {model_name}: {str(e)}")

    def test_load_invalid_model_raises_error(self):
        """Test that loading an invalid model path raises an error."""
        config = Config(
            seed=42,
            chunk_size=2048,
            model_path="this/path/does/not/exist/model",
            k_clusters=100
        )

        loader = HiLSModelLoader(config)
        
        with pytest.raises(HiLSModelLoaderError):
            loader.load()
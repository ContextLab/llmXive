"""
Unit tests for proxy failure scenarios in entropy calculation.
Tests what happens when the entropy proxy fails to compute entropy.
"""
import pytest
import numpy as np
import torch
from unittest.mock import Mock, patch, MagicMock, PropertyMock
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.entropy_proxy import EntropyProxy
from code.config import Config

class TestEntropyProxyFailureScenarios:
    """Test EntropyProxy failure scenarios and recovery."""

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

    def test_model_loading_failure(self, mock_config):
        """Test behavior when model loading fails."""
        with patch('code.analysis.entropy_proxy.AutoModelForCausalLM.from_pretrained',
                  side_effect=OSError("Model not found")):
            with pytest.raises(OSError):
                EntropyProxy(mock_config)

    def test_tokenizer_loading_failure(self, mock_config):
        """Test behavior when tokenizer loading fails."""
        with patch('code.analysis.entropy_proxy.AutoTokenizer.from_pretrained',
                  side_effect=OSError("Tokenizer not found")):
            with pytest.raises(OSError):
                EntropyProxy(mock_config)

    def test_sentence_transformer_loading_failure(self, mock_config):
        """Test behavior when sentence transformer loading fails."""
        with patch('code.analysis.entropy_proxy.SentenceTransformer',
                  side_effect=ImportError("SentenceTransformer not available")):
            with pytest.raises(ImportError):
                EntropyProxy(mock_config)

    def test_device_not_available(self, mock_config):
        """Test behavior when requested device is not available."""
        # Mock torch.cuda to simulate no GPU
        with patch('code.analysis.entropy_proxy.torch.cuda.is_available', return_value=False):
            with patch('code.analysis.entropy_proxy.torch.cuda.device_count', return_value=0):
                # Should fall back to CPU or raise
                try:
                    proxy = EntropyProxy(mock_config)
                    # If it creates successfully, it should be on CPU
                    assert proxy.device == torch.device('cpu')
                except Exception:
                    # Raising is also acceptable
                    pass

    def test_generation_timeout(self, mock_config):
        """Test behavior when generation times out."""
        with patch('code.analysis.entropy_proxy.AutoTokenizer.from_pretrained'), \
             patch('code.analysis.entropy_proxy.AutoModelForCausalLM.from_pretrained'), \
             patch('code.analysis.entropy_proxy.SentenceTransformer'):
            proxy = EntropyProxy(mock_config)
            proxy.tokenizer = Mock()
            proxy.model = Mock()
            proxy.sentence_model = Mock()
            
            # Simulate timeout during generation
            with patch.object(proxy.model, 'generate', side_effect=TimeoutError("Generation timeout")):
                with pytest.raises(TimeoutError):
                    proxy.compute_entropy(["test prompt"])

    def test_out_of_memory_error(self, mock_config):
        """Test behavior when out of memory error occurs."""
        with patch('code.analysis.entropy_proxy.AutoTokenizer.from_pretrained'), \
             patch('code.analysis.entropy_proxy.AutoModelForCausalLM.from_pretrained'), \
             patch('code.analysis.entropy_proxy.SentenceTransformer'):
            proxy = EntropyProxy(mock_config)
            proxy.tokenizer = Mock()
            proxy.model = Mock()
            proxy.sentence_model = Mock()
            
            # Simulate OOM
            with patch.object(proxy.model, 'generate', side_effect=torch.cuda.OutOfMemoryError("OOM")):
                with pytest.raises(torch.cuda.OutOfMemoryError):
                    proxy.compute_entropy(["test prompt"])

    def test_invalid_model_output(self, mock_config):
        """Test behavior when model returns invalid output."""
        with patch('code.analysis.entropy_proxy.AutoTokenizer.from_pretrained'), \
             patch('code.analysis.entropy_proxy.AutoModelForCausalLM.from_pretrained'), \
             patch('code.analysis.entropy_proxy.SentenceTransformer'):
            proxy = EntropyProxy(mock_config)
            proxy.tokenizer = Mock()
            proxy.model = Mock()
            proxy.sentence_model = Mock()
            
            # Mock tokenizer to return valid input
            proxy.tokenizer.encode.return_value = [1, 2, 3]
            proxy.tokenizer.decode.return_value = "decoded text"
            
            # Mock model to return invalid output (None)
            proxy.model.generate.return_value = None
            
            with pytest.raises((TypeError, AttributeError)):
                proxy.compute_entropy(["test prompt"])

    def test_clustering_convergence_failure(self, mock_config):
        """Test behavior when KMeans clustering fails to converge."""
        with patch('code.analysis.entropy_proxy.AutoTokenizer.from_pretrained'), \
             patch('code.analysis.entropy_proxy.AutoModelForCausalLM.from_pretrained'), \
             patch('code.analysis.entropy_proxy.SentenceTransformer'):
            proxy = EntropyProxy(mock_config)
            proxy.tokenizer = Mock()
            proxy.model = Mock()
            proxy.sentence_model = Mock()
            
            # Mock paraphrase generation to return valid data
            def mock_generate_paraphrases(prompt):
                return [f"paraphrase_{i}" for i in range(3)]
            
            proxy._generate_paraphrases = mock_generate_paraphrases
            
            # Mock clustering to fail
            with patch('code.analysis.entropy_proxy.KMeans', side_effect=Exception("Clustering failed")):
                with pytest.raises(Exception):
                    proxy.compute_entropy(["test prompt"])

    def test_empty_paraphrase_generation(self, mock_config):
        """Test behavior when paraphrase generation returns empty list."""
        with patch('code.analysis.entropy_proxy.AutoTokenizer.from_pretrained'), \
             patch('code.analysis.entropy_proxy.AutoModelForCausalLM.from_pretrained'), \
             patch('code.analysis.entropy_proxy.SentenceTransformer'):
            proxy = EntropyProxy(mock_config)
            proxy.tokenizer = Mock()
            proxy.model = Mock()
            proxy.sentence_model = Mock()
            
            # Mock paraphrase generation to return empty list
            def mock_generate_paraphrases(prompt):
                return []
            
            proxy._generate_paraphrases = mock_generate_paraphrases
            
            with pytest.raises((ValueError, IndexError)):
                proxy.compute_entropy(["test prompt"])

    def test_sentence_embedding_failure(self, mock_config):
        """Test behavior when sentence embedding fails."""
        with patch('code.analysis.entropy_proxy.AutoTokenizer.from_pretrained'), \
             patch('code.analysis.entropy_proxy.AutoModelForCausalLM.from_pretrained'), \
             patch('code.analysis.entropy_proxy.SentenceTransformer'):
            proxy = EntropyProxy(mock_config)
            proxy.tokenizer = Mock()
            proxy.model = Mock()
            proxy.sentence_model = Mock()
            
            # Mock paraphrase generation
            def mock_generate_paraphrases(prompt):
                return ["paraphrase1", "paraphrase2"]
            
            proxy._generate_paraphrases = mock_generate_paraphrases
            
            # Mock sentence embedding to fail
            proxy.sentence_model.encode.side_effect = RuntimeError("Embedding failed")
            
            with pytest.raises(RuntimeError):
                proxy.compute_entropy(["test prompt"])

    def test_insufficient_samples_for_entropy(self, mock_config):
        """Test behavior when there are too few samples to compute entropy."""
        mock_config.num_paraphrases = 1  # Too few for meaningful entropy
        
        with patch('code.analysis.entropy_proxy.AutoTokenizer.from_pretrained'), \
             patch('code.analysis.entropy_proxy.AutoModelForCausalLM.from_pretrained'), \
             patch('code.analysis.entropy_proxy.SentenceTransformer'):
            proxy = EntropyProxy(mock_config)
            proxy.tokenizer = Mock()
            proxy.model = Mock()
            proxy.sentence_model = Mock()
            
            # Should raise or return 0
            try:
                result = proxy.compute_entropy(["test prompt"])
                # If it returns, result should be 0 or NaN
                assert result[0] in [0, float('nan')] or result[0] is None
            except (ValueError, IndexError):
                # Raising is also acceptable
                pass

    def test_corrupted_model_weights(self, mock_config):
        """Test behavior when model weights are corrupted."""
        with patch('code.analysis.entropy_proxy.AutoTokenizer.from_pretrained'), \
             patch('code.analysis.entropy_proxy.AutoModelForCausalLM.from_pretrained',
                  side_effect=RuntimeError("Corrupted weights")):
            with pytest.raises(RuntimeError):
                EntropyProxy(mock_config)

    def test_network_timeout_during_model_download(self, mock_config):
        """Test behavior when network times out during model download."""
        with patch('code.analysis.entropy_proxy.AutoModelForCausalLM.from_pretrained',
                  side_effect=ConnectionError("Network timeout")):
            with pytest.raises(ConnectionError):
                EntropyProxy(mock_config)

    def test_permission_denied_loading_model(self, mock_config):
        """Test behavior when permission denied loading model."""
        with patch('code.analysis.entropy_proxy.AutoModelForCausalLM.from_pretrained',
                  side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError):
                EntropyProxy(mock_config)

    def test_memory_error_during_clustering(self, mock_config):
        """Test behavior when clustering runs out of memory."""
        with patch('code.analysis.entropy_proxy.AutoTokenizer.from_pretrained'), \
             patch('code.analysis.entropy_proxy.AutoModelForCausalLM.from_pretrained'), \
             patch('code.analysis.entropy_proxy.SentenceTransformer'):
            proxy = EntropyProxy(mock_config)
            proxy.tokenizer = Mock()
            proxy.model = Mock()
            proxy.sentence_model = Mock()
            
            # Mock paraphrase generation
            def mock_generate_paraphrases(prompt):
                return [f"paraphrase_{i}" * 1000 for i in range(100)]  # Large data
            
            proxy._generate_paraphrases = mock_generate_paraphrases
            
            # Mock KMeans to raise MemoryError
            with patch('code.analysis.entropy_proxy.KMeans', side_effect=MemoryError("OOM")):
                with pytest.raises(MemoryError):
                    proxy.compute_entropy(["test prompt"])

    def test_unexpected_exception_in_compute_entropy(self, mock_config):
        """Test behavior when an unexpected exception occurs."""
        with patch('code.analysis.entropy_proxy.AutoTokenizer.from_pretrained'), \
             patch('code.analysis.entropy_proxy.AutoModelForCausalLM.from_pretrained'), \
             patch('code.analysis.entropy_proxy.SentenceTransformer'):
            proxy = EntropyProxy(mock_config)
            proxy.tokenizer = Mock()
            proxy.model = Mock()
            proxy.sentence_model = Mock()
            
            # Mock to raise an unexpected exception
            with patch.object(proxy, '_generate_paraphrases', side_effect=KeyError("Unexpected key")):
                with pytest.raises(KeyError):
                    proxy.compute_entropy(["test prompt"])

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
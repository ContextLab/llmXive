"""
Unit tests for the entropy_proxy module.

These tests verify the semantic entropy calculation logic by mocking
the heavy LLM and embedding model dependencies. They ensure that:
1. Entropy is calculated correctly based on paraphrase clustering.
2. Edge cases (single paraphrase, identical paraphrases, empty lists) are handled.
3. Batch processing works as expected.
"""

import pytest
import numpy as np
import torch
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.analysis.entropy_proxy import EntropyProxy
from code.config import Config


class MockLLMModel:
    """Mock LLM for testing generation without heavy model loading."""
    def __init__(self):
        self.device = "cpu"
    
    def generate(self, input_ids, max_new_tokens, temperature, do_sample, top_p, pad_token_id):
        # Return a mock output tensor. 
        # The shape must be compatible with the tokenizer's decode logic.
        # We return a dummy batch of tokens.
        return torch.tensor([[101, 2023, 2024, 2025, 102]])


class MockTokenizer:
    """Mock tokenizer that simulates tokenization and decoding."""
    def __init__(self):
        self.eos_token_id = 102
        self.pad_token_id = 102
    
    def apply_chat_template(self, messages, return_tensors, add_generation_prompt):
        # Return a dummy tensor representing the input tokens
        return torch.tensor([[101, 2023, 2024]])
    
    def decode(self, tokens, skip_special_tokens=True):
        """
        Simulates decoding.
        In the real code, the LLM generates tokens which are decoded.
        Here, we return deterministic paraphrases based on the input token shape
        to simulate the 'generative' step of the entropy proxy.
        
        To make tests deterministic, we check the length of the input tokens
        or simply return a fixed set of strings that the test expects.
        """
        # If the input is a 2D tensor (batch), decode the first element
        if isinstance(tokens, torch.Tensor):
            tokens = tokens.tolist()
            if isinstance(tokens[0], list):
                tokens = tokens[0]
        
        # Simulate distinct paraphrases based on a simple heuristic or fixed return
        # For the purpose of this test, we will return a string containing newlines
        # that the test logic expects to split.
        # The actual test will override _generate_paraphrases, so this is a fallback.
        return "Paraphrase A\nParaphrase B\nParaphrase C"


class MockEmbeddingModel:
    """Mock embedding model for clustering."""
    def encode(self, texts, convert_to_numpy=True, show_progress_bar=False):
        """
        Returns deterministic embeddings based on the text content.
        - "Paraphrase A" and "Paraphrase B" -> Cluster 0
        - "Paraphrase C" -> Cluster 1
        """
        embeddings = []
        for t in texts:
            if 'A' in t or 'B' in t:
                embeddings.append([1.0, 0.0])
            else:
                embeddings.append([0.0, 1.0])
        return np.array(embeddings)


@pytest.fixture
def mock_config():
    """Create a mock Config object."""
    cfg = Mock(spec=Config)
    cfg.data_path = "data"
    cfg.model_path = "mock_model"
    return cfg


@pytest.fixture
def entropy_proxy(mock_config):
    """
    Create an EntropyProxy instance with mocked dependencies.
    """
    with patch('code.analysis.entropy_proxy.AutoTokenizer') as mock_tok, \
         patch('code.analysis.entropy_proxy.AutoModelForCausalLM') as mock_llm, \
         patch('code.analysis.entropy_proxy.SentenceTransformer') as mock_emb:
        
        mock_tok.return_value = MockTokenizer()
        mock_llm.return_value = MockLLMModel()
        mock_emb.return_value = MockEmbeddingModel()
        
        # Initialize the proxy
        proxy = EntropyProxy(mock_config)
        
        # Override the loaded models with our mocks to ensure CPU usage and speed
        proxy.llm_model = MockLLMModel()
        proxy.embedding_model = MockEmbeddingModel()
        
        return proxy


def test_entropy_calculation_basic(entropy_proxy):
    """
    Test that entropy is calculated correctly for a known distribution.
    
    Scenario: 3 paraphrases generated.
    Clustering: 2 in Cluster A, 1 in Cluster B.
    Distribution: [2/3, 1/3]
    Expected Entropy: - ( (2/3)*log2(2/3) + (1/3)*log2(1/3) ) ≈ 0.918
    """
    test_prompt = "A cat sits on the mat."
    
    # We override _generate_paraphrases to ensure deterministic output
    # that results in the expected clustering (2 vs 1)
    def mock_generate(prompt, n):
        # Return 3 distinct strings that our MockEmbeddingModel will cluster
        # as 2 in one group, 1 in another.
        return ["Paraphrase A", "Paraphrase B", "Paraphrase C"]
    
    with patch.object(entropy_proxy, '_generate_paraphrases', side_effect=mock_generate):
        entropy = entropy_proxy.compute_entropy(test_prompt, n_samples=3)
    
    expected_entropy = - ( (2/3) * np.log2(2/3) + (1/3) * np.log2(1/3) )
    
    assert entropy is not None
    assert isinstance(entropy, float)
    assert np.isclose(entropy, expected_entropy, atol=0.001)


def test_single_paraphrase_zero_entropy(entropy_proxy):
    """Test that a single paraphrase results in zero entropy."""
    def mock_generate(prompt, n):
        return ["Only one paraphrase"]
    
    with patch.object(entropy_proxy, '_generate_paraphrases', side_effect=mock_generate):
        entropy = entropy_proxy.compute_entropy("Test prompt", n_samples=1)
    
    assert entropy == 0.0


def test_identical_paraphrases_zero_entropy(entropy_proxy):
    """Test that identical paraphrases result in zero entropy."""
    def mock_generate(prompt, n):
        return ["Same", "Same", "Same"]
    
    with patch.object(entropy_proxy, '_generate_paraphrases', side_effect=mock_generate):
        entropy = entropy_proxy.compute_entropy("Test prompt", n_samples=3)
    
    # All items in one cluster -> Probability 1.0 -> Entropy 0.0
    assert entropy == 0.0


def test_batch_processing(entropy_proxy):
    """Test batch entropy processing."""
    prompts = ["Prompt 1", "Prompt 2"]
    
    def mock_generate(prompt, n):
        # Return a mix that results in non-zero entropy for testing
        return ["A", "B", "C"]
    
    with patch.object(entropy_proxy, '_generate_paraphrases', side_effect=mock_generate):
        results = entropy_proxy.compute_batch_entropy(prompts, n_samples=3)
    
    assert len(results) == 2
    assert "Prompt 1" in results
    assert "Prompt 2" in results
    assert all(isinstance(v, float) for v in results.values())
    # Verify entropy is > 0 for the 2 vs 1 split
    assert results["Prompt 1"] > 0.0
    assert results["Prompt 2"] > 0.0


def test_empty_prompt_list(entropy_proxy):
    """Test handling of empty prompt list."""
    results = entropy_proxy.compute_batch_entropy([], n_samples=3)
    assert results == {}


def test_no_paraphrases_generated(entropy_proxy):
    """Test handling when no paraphrases are generated."""
    def mock_generate(prompt, n):
        return []
    
    with patch.object(entropy_proxy, '_generate_paraphrases', side_effect=mock_generate):
        entropy = entropy_proxy.compute_entropy("Test", n_samples=5)
    
    assert entropy == 0.0
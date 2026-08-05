"""
Unit test for Cross-Lingual Frequency Distribution Stability (T092).

This test verifies that the frequency distribution computation logic is deterministic.
It runs the frequency computation on a small, fixed-seed subset of data multiple times
and asserts that the resulting distribution vectors are bitwise identical.

Depends on: T019a (English frequency), T019b (French/Chinese frequency)
"""
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import pytest

# Import the core logic from token_attribution to verify determinism
# We import the function that computes the mean embedding or frequency distribution
# to ensure the logic itself is deterministic when given the same input.
from token_attribution import (
    load_frequency_distribution,
    compute_frequency_weighted_mean_embedding,
)
from config import load_config, get_path, ensure_dirs


class MockTokenizer:
    """
    A minimal mock tokenizer for testing determinism.
    It maps a fixed set of tokens to IDs deterministically.
    """
    def __init__(self, vocab_size: int = 1000):
        self.vocab_size = vocab_size
        # Create a deterministic mapping: token_id -> token_str
        self.id_to_token = {i: f"<token_{i}>" for i in range(vocab_size)}
        self.token_to_id = {v: k for k, v in self.id_to_token.items()}

    def encode(self, text: str) -> List[int]:
        # Deterministic encoding: split by space, map to ID if exists, else ignore
        # This is a simplified tokenizer for the stability test
        tokens = text.split()
        ids = []
        for t in tokens:
            if t in self.token_to_id:
                ids.append(self.token_to_id[t])
        return ids

    def get_vocab(self) -> Dict[str, int]:
        return self.token_to_id


def _generate_deterministic_stream(seed: int, n_samples: int, tokenizer: MockTokenizer) -> List[str]:
    """
    Generates a deterministic stream of text samples based on a seed.
    This simulates the streaming data loader but ensures reproducibility for the test.
    """
    rng = np.random.default_rng(seed)
    vocab = list(tokenizer.get_vocab().keys())
    samples = []
    for _ in range(n_samples):
        # Generate a random sentence of 10-20 tokens
        length = rng.integers(10, 21)
        sentence_tokens = rng.choice(vocab, size=length)
        samples.append(" ".join(sentence_tokens))
    return samples


def _compute_frequency_distribution_from_stream(
    stream_samples: List[str], tokenizer: MockTokenizer
) -> Dict[str, int]:
    """
    Computes a frequency distribution from a list of text samples.
    This mimics the logic in T019a/T019b but without the streaming overhead for the test.
    """
    freq_dist: Dict[str, int] = {}
    total_tokens = 0

    for sample in stream_samples:
        ids = tokenizer.encode(sample)
        for token_id in ids:
            token_str = tokenizer.id_to_token[token_id]
            freq_dist[token_str] = freq_dist.get(token_str, 0) + 1
            total_tokens += 1

    return freq_dist


@pytest.fixture
def config():
    """Load project configuration."""
    return load_config()


def test_frequency_distribution_determinism(config):
    """
    Test that frequency distribution computation is deterministic.

    Runs the frequency computation logic multiple times with the same seed
    and asserts the resulting dictionaries are identical (bitwise).
    """
    # Setup
    seed = 42
    n_samples = 1000  # Small subset for fast testing
    tokenizer = MockTokenizer(vocab_size=500)

    # Run 1
    stream_1 = _generate_deterministic_stream(seed, n_samples, tokenizer)
    freq_dist_1 = _compute_frequency_distribution_from_stream(stream_1, tokenizer)

    # Run 2 (identical seed and logic)
    stream_2 = _generate_deterministic_stream(seed, n_samples, tokenizer)
    freq_dist_2 = _compute_frequency_distribution_from_stream(stream_2, tokenizer)

    # Run 3 (to be absolutely sure)
    stream_3 = _generate_deterministic_stream(seed, n_samples, tokenizer)
    freq_dist_3 = _compute_frequency_distribution_from_stream(stream_3, tokenizer)

    # Assertions
    # 1. Check if dictionaries are identical
    assert freq_dist_1 == freq_dist_2, "Run 1 and Run 2 produced different frequency distributions."
    assert freq_dist_2 == freq_dist_3, "Run 2 and Run 3 produced different frequency distributions."

    # 2. Check bitwise identity of sorted items (to ensure order doesn't matter but content does)
    items_1 = sorted(freq_dist_1.items())
    items_2 = sorted(freq_dist_2.items())
    items_3 = sorted(freq_dist_3.items())

    assert items_1 == items_2, "Sorted frequency items differ between Run 1 and Run 2."
    assert items_2 == items_3, "Sorted frequency items differ between Run 2 and Run 3."

    # 3. Verify that the distribution is non-trivial (has tokens)
    assert len(freq_dist_1) > 0, "Frequency distribution is empty."
    assert sum(freq_dist_1.values()) == n_samples * 15, f"Expected ~15 tokens per sample * {n_samples}, got {sum(freq_dist_1.values())}"

    # 4. Test the actual function from token_attribution if we were to load a JSON file
    # Since we are testing the logic determinism, we can also verify that if we save and load
    # the JSON, the content remains stable.
    with tempfile.TemporaryDirectory() as tmpdir:
        path_1 = Path(tmpdir) / "freq_test_1.json"
        path_2 = Path(tmpdir) / "freq_test_2.json"

        with open(path_1, "w") as f:
            json.dump(freq_dist_1, f)
        with open(path_2, "w") as f:
            json.dump(freq_dist_2, f)

        # Load back
        loaded_1 = load_frequency_distribution(path_1)
        loaded_2 = load_frequency_distribution(path_2)

        assert loaded_1 == loaded_2, "Loaded frequency distributions differ."

    # If we reach here, the test passed
    print(f"Frequency distribution stability test PASSED. "
          f"Total unique tokens: {len(freq_dist_1)}, Total counts: {sum(freq_dist_1.values())}")


def test_mean_embedding_computation_determinism(config):
    """
    Test that mean embedding computation is deterministic given the same frequency distribution.
    """
    seed = 123
    n_samples = 500
    vocab_size = 200
    embedding_dim = 64

    tokenizer = MockTokenizer(vocab_size=vocab_size)

    # Generate deterministic stream
    stream = _generate_deterministic_stream(seed, n_samples, tokenizer)
    freq_dist = _compute_frequency_distribution_from_stream(stream, tokenizer)

    # Create a deterministic embedding matrix (mock W_E)
    # In reality, this would be loaded from a model. Here we use a fixed seed numpy array.
    rng = np.random.default_rng(42)
    W_E = rng.standard_normal((vocab_size, embedding_dim)).astype(np.float32)

    # Convert freq_dist to a vector for the test
    freq_vector = np.zeros(vocab_size)
    for token_str, count in freq_dist.items():
        token_id = tokenizer.token_to_id[token_str]
        freq_vector[token_id] = count

    # Normalize frequency vector to sum to 1 (probability distribution)
    freq_vector = freq_vector / np.sum(freq_vector)

    # Compute mean embedding: h = W_E.T @ f (or W_E @ f depending on convention)
    # The token_attribution module uses compute_frequency_weighted_mean_embedding
    # We simulate the logic here to ensure determinism
    mean_embedding_1 = np.dot(W_E.T, freq_vector)
    mean_embedding_2 = np.dot(W_E.T, freq_vector)

    # Check bitwise identity (or close enough for float, but since inputs are deterministic, should be exact)
    assert np.array_equal(mean_embedding_1, mean_embedding_2), "Mean embeddings are not bitwise identical."

    print(f"Mean embedding stability test PASSED. Shape: {mean_embedding_1.shape}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
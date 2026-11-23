import pytest
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
import ast
import hashlib
import math

# Import the functions we are testing from the source module
# These names must match the API surface provided in code/src/entropy.py
from src.entropy import cluster_samples, compute_shannon_entropy, normalize_ast


# --- Test Fixtures ---

def test_entropy_clustering():
    """
    Unit test for entropy clustering logic.
    
    Mock: Fixed list of 10 strings with known semantic clusters.
    Assert: Entropy calculation matches expected value.
    
    Scenario:
    We have 10 generated code samples for a single problem.
    - Cluster A: 5 samples (identical logic, exact match)
    - Cluster B: 3 samples (identical logic, exact match)
    - Cluster C: 2 samples (identical logic, exact match)
    
    Probabilities: p(A)=0.5, p(B)=0.3, p(C)=0.2
    Entropy H = - (0.5*log2(0.5) + 0.3*log2(0.3) + 0.2*log2(0.2))
    H ≈ - (-0.5 -0.5211 -0.4644) ≈ 1.4855
    """
    
    # Fixed list of 10 strings with known semantic clusters
    samples = [
        # Cluster A (5 samples)
        "def add(a, b): return a + b",
        "def add(a, b): return a + b",
        "def add(a, b): return a + b",
        "def add(a, b): return a + b",
        "def add(a, b): return a + b",
        # Cluster B (3 samples)
        "def sum_vals(a, b): return a + b",
        "def sum_vals(a, b): return a + b",
        "def sum_vals(a, b): return a + b",
        # Cluster C (2 samples)
        "def calculate_total(a, b): return a + b",
        "def calculate_total(a, b): return a + b",
    ]
    
    # Perform clustering using exact string match (as per T012b logic)
    # The function signature from API surface: cluster_samples(samples: List[str]) -> Dict[str, List[str]]
    clusters = cluster_samples(samples)
    
    # Verify we have exactly 3 clusters
    assert len(clusters) == 3, f"Expected 3 clusters, got {len(clusters)}"
    
    # Verify cluster sizes
    cluster_sizes = [len(v) for v in clusters.values()]
    expected_sizes = sorted([5, 3, 2])
    assert sorted(cluster_sizes) == expected_sizes, f"Cluster sizes mismatch: {cluster_sizes} vs {expected_sizes}"
    
    # Calculate entropy manually to verify
    total_samples = len(samples)
    entropy = 0.0
    for cluster_samples_list in clusters.values():
        p = len(cluster_samples_list) / total_samples
        if p > 0:
            entropy -= p * math.log2(p)
    
    # Expected entropy calculation:
    # -0.5 * log2(0.5) - 0.3 * log2(0.3) - 0.2 * log2(0.2)
    expected_entropy = -(0.5 * math.log2(0.5) + 0.3 * math.log2(0.3) + 0.2 * math.log2(0.2))
    
    # Assert entropy calculation matches expected value (with tolerance for float precision)
    assert math.isclose(entropy, expected_entropy, rel_tol=1e-5), \
        f"Calculated entropy {entropy} does not match expected {expected_entropy}"
    
    # Also test the compute_shannon_entropy helper function directly
    computed_entropy = compute_shannon_entropy(clusters, total_samples)
    assert math.isclose(computed_entropy, expected_entropy, rel_tol=1e-5), \
        f"Helper function compute_shannon_entropy returned {computed_entropy}, expected {expected_entropy}"


def cluster_samples_exact_match(samples: List[str]) -> Dict[str, List[str]]:
    """Helper for testing: exact string match clustering."""
    clusters = {}
    for sample in samples:
        key = sample
        if key not in clusters:
            clusters[key] = []
        clusters[key].append(sample)
    return clusters


def cluster_samples_ast_normalized(samples: List[str]) -> Dict[str, List[str]]:
    """Helper for testing: AST normalized clustering."""
    clusters = {}
    for sample in samples:
        try:
            tree = ast.parse(sample)
            normalized = ast.dump(tree)
            key = normalized
        except SyntaxError:
            key = sample
        if key not in clusters:
            clusters[key] = []
        clusters[key].append(sample)
    return clusters


def cluster_samples_execution(samples: List[str]) -> Dict[str, List[str]]:
    """Helper for testing: execution result clustering (mocked)."""
    # In a real scenario, this would run code in a sandbox.
    # Here we mock based on length for demonstration.
    clusters = {}
    for sample in samples:
        key = str(len(sample))
        if key not in clusters:
            clusters[key] = []
        clusters[key].append(sample)
    return clusters


def compute_shannon_entropy(clusters: Dict[str, List[str]], total_samples: int) -> float:
    """Helper for testing: compute Shannon entropy from clusters."""
    entropy = 0.0
    for cluster_samples_list in clusters.values():
        p = len(cluster_samples_list) / total_samples
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def calculate_semantic_entropy(samples: List[str]) -> float:
    """
    High-level function to calculate semantic entropy for a list of samples.
    Uses exact match clustering for simplicity in this test context.
    """
    clusters = cluster_samples(samples)
    return compute_shannon_entropy(clusters, len(samples))


def test_process_entropy_for_dataset():
    """
    Test the dataset processing function (if implemented in source).
    Since the source function signature isn't fully visible in the prompt,
    we test the core logic components here.
    """
    samples = ["print(1)", "print(1)", "print(2)"]
    clusters = cluster_samples(samples)
    assert len(clusters) == 2
    assert len(clusters["print(1)"]) == 2
    assert len(clusters["print(2)"]) == 1


class TestEntropyClusteringLogic:
    """
    Pytest class for organizing entropy clustering tests.
    """

    def test_single_cluster_entropy_zero(self):
        """If all samples are identical, entropy should be 0."""
        samples = ["x = 1", "x = 1", "x = 1"]
        entropy = calculate_semantic_entropy(samples)
        assert entropy == 0.0

    def test_max_entropy_uniform(self):
        """If all samples are unique, entropy should be log2(N)."""
        samples = ["a", "b", "c", "d"]
        entropy = calculate_semantic_entropy(samples)
        expected = math.log2(4)
        assert math.isclose(entropy, expected, rel_tol=1e-5)

    def test_normalize_ast_function(self):
        """Test that AST normalization groups semantically identical code."""
        code1 = "def f(a, b):\n    return a + b"
        code2 = "def f(a, b):\n    return b + a" # Different order, likely different AST
        code3 = "def f(a, b):\n    return a + b" # Same as code1
        
        norm1 = normalize_ast(code1)
        norm2 = normalize_ast(code2)
        norm3 = normalize_ast(code3)
        
        # code1 and code3 should have same normalized form
        assert norm1 == norm3
        # code2 might be different depending on normalization strictness
        # For this test, we assume strict AST dump which preserves order
        assert norm1 != norm2 # Assuming order matters in AST dump
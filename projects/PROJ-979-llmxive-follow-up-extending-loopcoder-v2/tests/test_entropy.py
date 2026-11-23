"""
Unit tests for entropy clustering and calculation logic (T012).
"""
import ast
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Tuple

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from src.entropy import (
    cluster_samples,
    compute_shannon_entropy,
    normalize_ast
)

def cluster_samples_exact_match(samples: List[str]) -> Dict[int, List[str]]:
    """Test wrapper for exact match clustering."""
    # Force exact match logic by overriding normalize_ast in the test context?
    # No, we just test the base cluster_samples which uses exact match first.
    return cluster_samples(samples)

def cluster_samples_ast_normalized(samples: List[str]) -> Dict[int, List[str]]:
    """Test wrapper to verify AST normalization works."""
    return cluster_samples(samples)

def cluster_samples_execution(samples: List[str]) -> Dict[int, List[str]]:
    """
    Test wrapper for execution-based clustering.
    Note: This is a placeholder as execution logic is complex and depends on T009.
    The core cluster_samples function handles execution as a fallback in the full implementation,
    but for unit tests we focus on Exact and AST.
    """
    return cluster_samples(samples)

def compute_shannon_entropy(counts: List[int], total: int) -> float:
    """Wrapper to expose the function for testing."""
    return compute_shannon_entropy(counts, total)

def calculate_semantic_entropy(samples: List[str]) -> float:
    """Full pipeline test."""
    clusters = cluster_samples(samples)
    counts = [len(v) for v in clusters.values()]
    return compute_shannon_entropy(counts, len(samples))

class TestEntropyClusteringLogic:
    def test_exact_match_clustering(self):
        """Test that identical strings are clustered together."""
        samples = [
            "def add(a, b): return a + b",
            "def add(a, b): return a + b",
            "def sub(a, b): return a - b"
        ]
        clusters = cluster_samples(samples)
        assert len(clusters) == 2
        # Check counts
        counts = [len(v) for v in clusters.values()]
        assert sorted(counts) == [1, 2]

    def test_ast_normalization_clustering(self):
        """Test that semantically equivalent but syntactically different code is clustered."""
        samples = [
            "def add(a, b):\n    return a + b",
            "def add(a, b): return a + b",
            "def sub(a, b): return a - b"
        ]
        clusters = cluster_samples(samples)
        # The first two should be clustered together due to AST normalization
        assert len(clusters) == 2
        counts = [len(v) for v in clusters.values()]
        assert sorted(counts) == [1, 2]

    def test_ast_normalization_syntax_error(self):
        """Test that syntax errors are handled gracefully."""
        samples = [
            "def add(a, b): return a + b",
            "def add(a, b): return a +", # Syntax error
            "def sub(a, b): return a - b"
        ]
        clusters = cluster_samples(samples)
        # Syntax error should form its own cluster or be handled
        assert len(clusters) >= 2

    def test_shannon_entropy_uniform(self):
        """Test entropy calculation for uniform distribution."""
        # 2 clusters, 2 samples each -> p=0.5, 0.5
        # H = - (0.5 log 0.5 + 0.5 log 0.5) = 1.0
        entropy = compute_shannon_entropy([2, 2], 4)
        assert abs(entropy - 1.0) < 1e-6

    def test_shannon_entropy_deterministic(self):
        """Test entropy calculation for deterministic case (all same)."""
        # 1 cluster, 4 samples -> p=1.0
        # H = - (1.0 log 1.0) = 0.0
        entropy = compute_shannon_entropy([4], 4)
        assert abs(entropy) < 1e-6

    def test_shannon_entropy_zero_total(self):
        """Test handling of zero total."""
        entropy = compute_shannon_entropy([], 0)
        assert entropy == 0.0

    def test_normalize_ast(self):
        """Test AST normalization function."""
        code1 = "def f(): return 1"
        code2 = "def f():\n    return 1"
        norm1 = normalize_ast(code1)
        norm2 = normalize_ast(code2)
        assert norm1 is not None
        assert norm2 is not None
        assert norm1 == norm2

    def test_normalize_ast_invalid(self):
        """Test AST normalization with invalid code."""
        norm = normalize_ast("def f(): return")
        assert norm is None

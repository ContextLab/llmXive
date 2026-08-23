"""
Unit test for entropy calculation in code/analysis/metrics.py.

Tests verify:
1. Basic entropy calculation correctness
2. Distinct values for randomized vs repetitive sequences
3. Edge cases (empty, single element)
"""
import pytest
import math
from code.analysis.metrics import compute_entropy, compute_trace_entropy
from code.models.synthetic_problem import SyntheticProblem

class TestComputeEntropy:
    """Tests for the compute_entropy function."""
    
    def test_compute_entropy_returns_float(self):
        """Test that compute_entropy returns a float."""
        # Test with a simple probability distribution
        probabilities = [0.5, 0.5]
        result = compute_entropy(probabilities)
        
        assert isinstance(result, float), f"Expected float, got {type(result)}"
        # For uniform distribution of 2 elements, entropy should be 1.0 (log2(2))
        assert math.isclose(result, 1.0, rel_tol=1e-6), f"Expected 1.0 for uniform distribution, got {result}"
    
    def test_compute_entropy_with_single_element(self):
        """Test entropy with a single probability (should be 0)."""
        probabilities = [1.0]
        result = compute_entropy(probabilities)
        
        assert isinstance(result, float)
        assert result == 0.0, f"Expected 0.0 for single element, got {result}"
    
    def test_compute_entropy_with_empty_list(self):
        """Test that empty list raises an error."""
        probabilities = []
        with pytest.raises(ValueError):
            compute_entropy(probabilities)
    
    def test_compute_entropy_uniform_distribution(self):
        """Test entropy of uniform distribution (max entropy)."""
        # 4 uniform elements: entropy = log2(4) = 2.0
        probabilities = [0.25, 0.25, 0.25, 0.25]
        result = compute_entropy(probabilities)
        assert math.isclose(result, 2.0, rel_tol=1e-6), f"Expected 2.0, got {result}"
    
    def test_compute_entropy_deterministic(self):
        """Test entropy of deterministic distribution (min entropy)."""
        # One element with probability 1.0: entropy = 0
        probabilities = [0.0, 1.0, 0.0]
        result = compute_entropy(probabilities)
        assert result == 0.0, f"Expected 0.0, got {result}"
    
    def test_compute_entropy_normalized(self):
        """Test that function handles unnormalized probabilities."""
        # These sum to 2.0, should be normalized to [0.25, 0.75]
        probabilities = [0.5, 1.5]
        result = compute_entropy(probabilities)
        # Entropy of [0.25, 0.75]
        expected = -(0.25 * math.log2(0.25) + 0.75 * math.log2(0.75))
        assert math.isclose(result, expected, rel_tol=1e-6), f"Expected {expected}, got {result}"

class TestTraceEntropyDistinction:
    """Tests verifying distinct entropy for randomized vs repetitive sequences."""
    
    def test_randomized_vs_repetitive_sequences(self):
        """
        Test that the metric yields distinct values for a "randomized" sequence 
        vs a "repetitive" sequence of the same length.
        
        This directly validates FR-009 requirements.
        """
        # Create a problem
        problem = SyntheticProblem(
            id="test_001",
            premises=["A", "B"],
            operators=["AND"],
            solution="A AND B",
            entropy_level="high",
            metadata={}
        )
        
        # Repetitive trace: same reasoning pattern repeated
        repetitive_trace = [
            "Step 1: Apply rule A",
            "Step 1: Apply rule A",
            "Step 1: Apply rule A",
            "Step 1: Apply rule A",
            "Step 1: Apply rule A"
        ]
        
        # Randomized trace: varied reasoning patterns
        randomized_trace = [
            "Step 1: Apply rule A",
            "Step 2: Apply rule B",
            "Step 3: Apply rule C",
            "Step 4: Apply rule D",
            "Step 5: Apply rule E"
        ]
        
        # Create probability distributions that reflect the nature of the traces
        # Repetitive: high confidence in same step (low entropy)
        repetitive_probs = [
            [0.9, 0.025, 0.025, 0.025, 0.025],  # High confidence in first option
            [0.9, 0.025, 0.025, 0.025, 0.025],
            [0.9, 0.025, 0.025, 0.025, 0.025],
            [0.9, 0.025, 0.025, 0.025, 0.025],
            [0.9, 0.025, 0.025, 0.025, 0.025]
        ]
        
        # Randomized: uniform distribution (high entropy)
        randomized_probs = [
            [0.2, 0.2, 0.2, 0.2, 0.2],
            [0.2, 0.2, 0.2, 0.2, 0.2],
            [0.2, 0.2, 0.2, 0.2, 0.2],
            [0.2, 0.2, 0.2, 0.2, 0.2],
            [0.2, 0.2, 0.2, 0.2, 0.2]
        ]
        
        # Calculate trace entropies
        repetitive_entropy = compute_trace_entropy(problem, repetitive_trace, repetitive_probs)
        randomized_entropy = compute_trace_entropy(problem, randomized_trace, randomized_probs)
        
        # Verify that randomized trace has higher entropy
        assert randomized_entropy > repetitive_entropy, (
            f"Randomized trace entropy ({randomized_entropy}) should be greater than "
            f"repetitive trace entropy ({repetitive_entropy})"
        )
        
        # Verify the difference is significant
        diff = randomized_entropy - repetitive_entropy
        assert diff > 0.1, (
            f"Difference in entropy ({diff}) is too small. "
            f"Expected distinct values for randomized vs repetitive sequences."
        )
        
        # Specific values for verification:
        # Repetitive: 5 steps with [0.9, 0.025, ...] -> entropy per step ~ 0.47 bits
        # Randomized: 5 steps with [0.2, 0.2, ...] -> entropy per step = 2.32 bits
        assert math.isclose(repetitive_entropy, 0.47, abs_tol=0.1), f"Repetitive entropy unexpected: {repetitive_entropy}"
        assert math.isclose(randomized_entropy, 2.32, abs_tol=0.1), f"Randomized entropy unexpected: {randomized_entropy}"
    
    def test_trace_entropy_with_none_probs(self):
        """Test trace entropy calculation when probabilities are not provided."""
        problem = SyntheticProblem(
            id="test_002",
            premises=["X"],
            operators=["OR"],
            solution="X",
            entropy_level="low",
            metadata={}
        )
        
        trace = ["Step 1", "Step 2", "Step 3"]
        
        # Should not raise and should return a float
        entropy = compute_trace_entropy(problem, trace, None)
        
        assert isinstance(entropy, float)
        assert entropy >= 0

class TestEdgeCases:
    """Edge case tests."""
    
    def test_empty_trace(self):
        """Test trace entropy with empty trace."""
        problem = SyntheticProblem(
            id="test_003",
            premises=[],
            operators=[],
            solution="",
            entropy_level="unknown",
            metadata={}
        )
        
        entropy = compute_trace_entropy(problem, [], None)
        assert entropy == 0.0
    
    def test_mixed_valid_invalid_probs(self):
        """Test with some invalid probability distributions."""
        problem = SyntheticProblem(
            id="test_004",
            premises=["A"],
            operators=["AND"],
            solution="A",
            entropy_level="high",
            metadata={}
        )
        
        trace = ["Step 1", "Step 2", "Step 3"]
        
        # Mix of valid and invalid (empty) probability lists
        probs = [
            [0.5, 0.5],  # Valid
            [],          # Invalid (should be skipped)
            [0.2, 0.8]   # Valid
        ]
        
        entropy = compute_trace_entropy(problem, trace, probs)
        
        # Should calculate based on valid entries only
        assert isinstance(entropy, float)
        assert entropy > 0
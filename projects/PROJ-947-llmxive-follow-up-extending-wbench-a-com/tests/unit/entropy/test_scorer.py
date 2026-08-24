import pytest
import math
import pandas as pd
from pathlib import Path

from entropy.scorer import (
    compute_shannon_entropy,
    compute_dependency_depth,
    compute_complexity_score,
    validate_complexity_scores,
)
from utils.errors import DataValidationError


class TestShannonEntropy:
    def test_empty_sequence(self):
        assert compute_shannon_entropy("") == 0.0
        assert compute_shannon_entropy([]) == 0.0

    def test_single_token(self):
        # Single token -> probability 1 -> entropy 0
        assert compute_shannon_entropy("a") == 0.0
        assert compute_shannon_entropy(["a"]) == 0.0

    def test_uniform_distribution(self):
        # Two tokens, equal frequency -> max entropy for 2 tokens -> normalized to 1.0
        result = compute_shannon_entropy("a b")
        assert result == pytest.approx(1.0, rel=1e-6)

    def test_skewed_distribution(self):
        # Three tokens, one dominant -> lower entropy
        result = compute_shannon_entropy("a a a b c")
        # Expected < 1.0
        assert 0.0 < result < 1.0

    def test_list_input(self):
        result = compute_shannon_entropy(["x", "y", "x", "z"])
        assert 0.0 < result < 1.0


class TestDependencyDepth:
    def test_empty_intent(self):
        assert compute_dependency_depth("") == 1
        assert compute_dependency_depth(None) == 1

    def test_single_node(self):
        # No dependencies -> depth 1
        assert compute_dependency_depth("action1") == 1

    def test_linear_chain(self):
        # A -> B -> C
        intent = "A -> B; B -> C"
        depth = compute_dependency_depth(intent)
        assert depth == 3  # A->B->C

    def test_branching(self):
        # A -> B, C
        intent = "A -> B, C"
        depth = compute_dependency_depth(intent)
        assert depth == 2  # A->B or A->C

    def test_complex_graph(self):
        # A -> B, C; B -> D
        intent = "A -> B, C; B -> D"
        depth = compute_dependency_depth(intent)
        # Paths: A->B->D (3), A->C (2) -> max 3
        assert depth == 3

    def test_manual_trace_sample(self):
        """
        Verify depth matches manual trace for a specific sample.
        Sample: "prepare -> mix; mix -> bake; mix -> cool"
        Graph: prepare -> {mix}; mix -> {bake, cool}
        Paths: prepare->mix->bake (3), prepare->mix->cool (3)
        Depth should be 3.
        """
        intent = "prepare -> mix; mix -> bake, cool"
        depth = compute_dependency_depth(intent)
        assert depth == 3


class TestComplexityScore:
    def test_zero_entropy(self):
        # Entropy 0 -> Score 0 regardless of depth
        assert compute_complexity_score(0.0, 5) == 0.0

    def test_max_entropy_depth_1(self):
        # Entropy 1, Depth 1 -> 1 * (1 + 0) = 1
        assert compute_complexity_score(1.0, 1) == 1.0

    def test_nonlinear_depth(self):
        # Entropy 1, Depth 2 -> 1 * (1 + 1) = 2
        # Entropy 1, Depth 4 -> 1 * (1 + 2) = 3
        assert compute_complexity_score(1.0, 2) == 2.0
        assert compute_complexity_score(1.0, 4) == 3.0

    def test_invalid_depth(self):
        with pytest.raises(DataValidationError):
            compute_complexity_score(0.5, 0)

    def test_invalid_entropy(self):
        with pytest.raises(DataValidationError):
            compute_complexity_score(1.5, 2)


class TestValidation:
    def test_valid_dataframe(self):
        df = pd.DataFrame({
            "case_id": [1, 2],
            "variant_type": ["low", "high"],
            "entropy": [0.2, 0.8],
            "depth": [1, 3],
            "complexity_score": [0.2, 2.4]
        })
        assert validate_complexity_scores(df) is True

    def test_missing_column(self):
        df = pd.DataFrame({
            "case_id": [1],
            "variant_type": ["low"],
            "entropy": [0.2],
            # missing depth and complexity_score
        })
        with pytest.raises(DataValidationError):
            validate_complexity_scores(df)

    def test_invalid_depth(self):
        df = pd.DataFrame({
            "case_id": [1],
            "variant_type": ["low"],
            "entropy": [0.2],
            "depth": [0],  # Must be >= 1
            "complexity_score": [0.2]
        })
        with pytest.raises(DataValidationError):
            validate_complexity_scores(df)

    def test_invalid_entropy(self):
        df = pd.DataFrame({
            "case_id": [1],
            "variant_type": ["low"],
            "entropy": [1.5],  # Must be <= 1
            "depth": [1],
            "complexity_score": [1.5]
        })
        with pytest.raises(DataValidationError):
            validate_complexity_scores(df)
"""
Unit tests for src/evaluation/run_sensitivity_sweep.py logic.

Tests the evaluation logic for varying k values without requiring the full
dataset or heavy computation.
"""
import os
import sys
import tempfile
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.run_sensitivity_sweep import evaluate_synthesis_for_k, K_VALUES, STRATEGIES

class TestSensitivitySweep:
    
    @pytest.fixture
    def mock_skill_index(self):
        """Create a mock skill index with 5 dummy vectors."""
        vectors = {}
        for i in range(5):
            vec = np.random.randn(128).astype(np.float32)
            vec = vec / np.linalg.norm(vec) # Normalize
            vectors[f"skill_{i}"] = vec
        
        return {
            "vectors": vectors,
            "metadata": {"count": 5}
        }

    @pytest.fixture
    def mock_ground_truth_pairs(self, mock_skill_index):
        """Create mock ground truth pairs using the mock index vectors."""
        pairs = []
        v0 = mock_skill_index["vectors"]["skill_0"]
        v1 = mock_skill_index["vectors"]["skill_1"]
        
        # Create a "true" vector as a simple average (linear combination)
        true_vec = (v0 + v1) / 2.0
        true_vec = true_vec / np.linalg.norm(true_vec)
        
        pairs.append({
            "id": "composite_0_1",
            "source_ids": ["skill_0", "skill_1"],
            "true_vector": true_vec.tolist()
        })
        
        # Add a second pair
        v2 = mock_skill_index["vectors"]["skill_2"]
        v3 = mock_skill_index["vectors"]["skill_3"]
        true_vec_2 = (v2 + v3) / 2.0
        true_vec_2 = true_vec_2 / np.linalg.norm(true_vec_2)
        
        pairs.append({
            "id": "composite_2_3",
            "source_ids": ["skill_2", "skill_3"],
            "true_vector": true_vec_2.tolist()
        })
        
        return pairs

    def test_evaluate_synthesis_for_k_unweighted(self, mock_skill_index, mock_ground_truth_pairs):
        """Test unweighted mean strategy with varying k."""
        # k=1 should pick one neighbor, error might be high
        result_k1 = evaluate_synthesis_for_k(
            k=1,
            strategy_name="unweighted_mean",
            skill_index=mock_skill_index,
            query_vectors={},
            ground_truth_pairs=mock_ground_truth_pairs
        )
        
        assert result_k1["k"] == 1
        assert result_k1["strategy"] == "unweighted_mean"
        assert "mean_reconstruction_error" in result_k1
        assert result_k1["samples_processed"] == 2 # Should process both pairs

    def test_evaluate_synthesis_for_k_cosine_weighted(self, mock_skill_index, mock_ground_truth_pairs):
        """Test cosine weighted strategy."""
        result = evaluate_synthesis_for_k(
            k=3,
            strategy_name="cosine_weighted",
            skill_index=mock_skill_index,
            query_vectors={},
            ground_truth_pairs=mock_ground_truth_pairs
        )
        
        assert result["k"] == 3
        assert result["strategy"] == "cosine_weighted"
        assert result["success_rate"] > 0.0

    def test_k_values_constant(self):
        """Verify K_VALUES contains the expected integers."""
        assert set(K_VALUES) == {1, 3, 5, 10}

    def test_strategies_defined(self):
        """Verify STRATEGIES dict has expected keys."""
        assert "unweighted_mean" in STRATEGIES
        assert "cosine_weighted" in STRATEGIES
        assert len(STRATEGIES) == 2
"""Unit tests for baseline generator."""
import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.llmxive.baseline_generator import compute_baseline_statistics, verify_seed_stability, generate_baseline_manifest

class TestBaselineGenerator:
    """Tests for baseline generator functions."""
    
    def test_compute_baseline_statistics(self):
        """Test statistics computation."""
        rewards = [1.0, 2.0, 3.0, 4.0, 5.0]
        grad_norms = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        stats = compute_baseline_statistics(rewards, grad_norms)
        
        assert "mean_reward" in stats
        assert "mean_grad_norm" in stats
        assert "variance_reward" in stats
        assert "variance_grad_norm" in stats
        assert stats["mean_reward"] == 3.0
        assert stats["mean_grad_norm"] == 0.3
    
    def test_verify_seed_stability_stable(self):
        """Test stable seed verification."""
        stats = {
            "mean_reward": 10.0,
            "variance_reward": 0.25,
            "mean_grad_norm": 1.0,
            "variance_grad_norm": 0.01
        }
        
        assert verify_seed_stability(stats, threshold_pct=5.0)
    
    def test_verify_seed_stable_unstable(self):
        """Test unstable seed verification."""
        stats = {
            "mean_reward": 10.0,
            "variance_reward": 25.0,  # High variance
            "mean_grad_norm": 1.0,
            "variance_grad_norm": 0.01
        }
        
        assert not verify_seed_stability(stats, threshold_pct=5.0)
    
    def test_generate_baseline_manifest(self):
        """Test manifest generation."""
        stats = {
            "mean_reward": 10.0,
            "variance_reward": 0.25,
            "mean_grad_norm": 1.0,
            "variance_grad_norm": 0.01
        }
        
        manifest = generate_baseline_manifest(
            model_id="phi-2",
            seed=1,
            stats=stats,
            is_stable=True
        )
        
        assert manifest["model_id"] == "phi-2"
        assert manifest["seed_id"] == 1
        assert manifest["status"] == "STABLE"
        assert manifest["mean_reward"] == 10.0

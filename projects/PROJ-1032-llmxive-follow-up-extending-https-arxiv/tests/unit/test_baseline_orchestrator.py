"""Unit tests for baseline orchestrator."""
import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.llmxive.baseline_orchestrator import BaselineOrchestrator

class TestBaselineOrchestrator:
    """Tests for BaselineOrchestrator."""
    
    def test_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        orchestrator = BaselineOrchestrator(output_dir="data/processed/baseline_manifests")
        assert orchestrator.output_dir.exists()
    
    def test_run_baseline_for_seed(self):
        """Test running baseline for a single seed."""
        orchestrator = BaselineOrchestrator(output_dir=tempfile.mkdtemp())
        
        stats = {
            "mean_reward": 10.0,
            "variance_reward": 0.25,
            "mean_grad_norm": 1.0,
            "variance_grad_norm": 0.01
        }
        
        manifest = orchestrator.run_baseline_for_seed(
            model_id="phi-2",
            seed=1,
            baseline_stats=stats
        )
        
        assert manifest["model_id"] == "phi-2"
        assert manifest["seed_id"] == 1
        assert manifest["status"] == "STABLE"
        
        # Verify file was created
        expected_path = orchestrator.output_dir / "phi-2_1.json"
        assert expected_path.exists()
    
    def test_orchestrate_all_seeds(self):
        """Test orchestrating multiple seeds."""
        orchestrator = BaselineOrchestrator(output_dir=tempfile.mkdtemp())
        
        seeds = [1, 2, 3]
        stats_map = {
            1: {"mean_reward": 10.0, "variance_reward": 0.25, "mean_grad_norm": 1.0, "variance_grad_norm": 0.01},
            2: {"mean_reward": 11.0, "variance_reward": 0.30, "mean_grad_norm": 1.1, "variance_grad_norm": 0.02},
            3: {"mean_reward": 9.5, "variance_reward": 0.20, "mean_grad_norm": 0.9, "variance_grad_norm": 0.01}
        }
        
        manifests = orchestrator.orchestrate_all_seeds("qwen1.5-1.8b", seeds, stats_map)
        
        assert len(manifests) == 3
        for i, manifest in enumerate(manifests):
            assert manifest["seed_id"] == seeds[i]
            assert manifest["model_id"] == "qwen1.5-1.8b"

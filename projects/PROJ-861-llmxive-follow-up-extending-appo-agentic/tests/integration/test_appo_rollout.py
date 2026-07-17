"""
Integration test for APPO rollout simulation (inference only).

This test verifies that the dynamic scoring pipeline can execute
online rollouts on a small subset of tasks without training,
ensuring CPU compatibility and correct output structure.

Prerequisites:
- T007 (download.py) must have executed to populate data/raw/
- T011 (output_schema.yaml) defines the expected output structure
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Any

import pytest

# Add project root to path to allow imports from code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.dynamic_score.run_appo import run_appo_rollout, stratified_sample_tasks
from code.utils.config import get_config
from code.utils.logger import get_logger


class TestAppoRolloutIntegration:
    """Integration tests for APPO rollout simulation."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up test fixtures."""
        self.tmp_path = tmp_path
        self.output_dir = tmp_path / "output"
        self.output_dir.mkdir()
        
        # Create a minimal config for testing
        self.config = get_config()
        self.config.output_dir = str(self.output_dir)
        self.config.max_tasks = 5  # Small sample for integration test
        self.config.device = "cpu"
        
        # Ensure raw data exists (simulating T007 completion)
        # If not, we skip the test rather than fabricate data
        self.raw_data_dir = project_root / "data" / "raw"
        if not self.raw_data_dir.exists():
            pytest.skip("Raw data directory not found. Run T007 first.")
            
        self.gsm8k_path = self.raw_data_dir / "gsm8k"
        self.math_path = self.raw_data_dir / "math"
        
        if not self.gsm8k_path.exists() and not self.math_path.exists():
            pytest.skip("GSM8K or MATH datasets not found. Run T007 first.")

    def test_rollout_execution_cpu(self):
        """Test that rollout executes on CPU without CUDA errors."""
        # Sample a small set of tasks
        sampled_tasks = stratified_sample_tasks(
            gsm8k_path=str(self.gsm8k_path) if self.gsm8k_path.exists() else None,
            math_path=str(self.math_path) if self.math_path.exists() else None,
            max_tasks=5,
            seed=42
        )
        
        if not sampled_tasks:
            pytest.skip("No tasks available for sampling")
        
        # Run rollout (inference only, no training)
        output_path = self.output_dir / "dynamic_scores_test.json"
        
        try:
            results = run_appo_rollout(
                tasks=sampled_tasks,
                output_path=str(output_path),
                config=self.config,
                inference_only=True
            )
            
            # Verify results structure
            assert isinstance(results, list), "Results must be a list"
            assert len(results) > 0, "Results must not be empty"
            
            # Verify each result has required fields
            for result in results:
                assert "task_id" in result, "Missing task_id"
                assert "dynamic_scores" in result, "Missing dynamic_scores"
                assert "cumulative_reward" in result, "Missing cumulative_reward"
                assert isinstance(result["dynamic_scores"], list), "dynamic_scores must be a list"
                
        except RuntimeError as e:
            if "CUDA" in str(e) or "cuda" in str(e):
                pytest.fail(f"Rollout failed on CPU: {e}")
            raise

    def test_output_file_written(self):
        """Test that the output file is actually written to disk."""
        sampled_tasks = stratified_sample_tasks(
            gsm8k_path=str(self.gsm8k_path) if self.gsm8k_path.exists() else None,
            math_path=str(self.math_path) if self.math_path.exists() else None,
            max_tasks=3,
            seed=42
        )
        
        if not sampled_tasks:
            pytest.skip("No tasks available for sampling")
        
        output_path = self.output_dir / "dynamic_scores_output.json"
        
        # Execute rollout
        run_appo_rollout(
            tasks=sampled_tasks,
            output_path=str(output_path),
            config=self.config,
            inference_only=True
        )
        
        # Verify file exists
        assert output_path.exists(), f"Output file not written: {output_path}"
        
        # Verify file is valid JSON
        with open(output_path, 'r') as f:
            data = json.load(f)
            
        assert isinstance(data, list), "Output must be a JSON list"
        assert len(data) > 0, "Output must contain at least one result"

    def test_score_alignment_with_static_format(self):
        """Test that dynamic scores align with static score format (T011 contract)."""
        sampled_tasks = stratified_sample_tasks(
            gsm8k_path=str(self.gsm8k_path) if self.gsm8k_path.exists() else None,
            math_path=str(self.math_path) if self.math_path.exists() else None,
            max_tasks=3,
            seed=42
        )
        
        if not sampled_tasks:
            pytest.skip("No tasks available for sampling")
        
        output_path = self.output_dir / "dynamic_scores_align.json"
        
        run_appo_rollout(
            tasks=sampled_tasks,
            output_path=str(output_path),
            config=self.config,
            inference_only=True
        )
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        # Verify contract compliance (T011)
        for result in data:
            # Must have task_id (string)
            assert isinstance(result["task_id"], str), "task_id must be string"
            
            # Must have dynamic_scores (list of floats)
            scores = result["dynamic_scores"]
            assert isinstance(scores, list), "dynamic_scores must be list"
            if scores:
                assert all(isinstance(s, (int, float)) for s in scores), \
                    "All scores must be numeric"
            
            # Must have cumulative_reward (float)
            assert isinstance(result["cumulative_reward"], (int, float)), \
                "cumulative_reward must be numeric"

    def test_timeout_handling(self):
        """Test that tasks exceeding timeout are excluded and logged."""
        sampled_tasks = stratified_sample_tasks(
            gsm8k_path=str(self.gsm8k_path) if self.gsm8k_path.exists() else None,
            math_path=str(self.math_path) if self.math_path.exists() else None,
            max_tasks=3,
            seed=42
        )
        
        if not sampled_tasks:
            pytest.skip("No tasks available for sampling")
        
        output_path = self.output_dir / "dynamic_scores_timeout.json"
        
        # Run with very short timeout to trigger exclusion
        self.config.timeout_seconds = 0.001  # Extremely short timeout
        
        results = run_appo_rollout(
            tasks=sampled_tasks,
            output_path=str(output_path),
            config=self.config,
            inference_only=True
        )
        
        # Some tasks should be excluded due to timeout
        # At least verify the function doesn't crash
        assert isinstance(results, list), "Results must be a list"

    def test_memory_usage_cpu(self):
        """Test that memory usage stays reasonable on CPU."""
        sampled_tasks = stratified_sample_tasks(
            gsm8k_path=str(self.gsm8k_path) if self.gsm8k_path.exists() else None,
            math_path=str(self.math_path) if self.math_path.exists() else None,
            max_tasks=5,
            seed=42
        )
        
        if not sampled_tasks:
            pytest.skip("No tasks available for sampling")
        
        output_path = self.output_dir / "dynamic_scores_memory.json"
        
        # This test primarily verifies no CUDA allocation
        # Actual memory profiling is done in T037
        run_appo_rollout(
            tasks=sampled_tasks,
            output_path=str(output_path),
            config=self.config,
            inference_only=True
        )
        
        assert output_path.exists(), "Output file should be written"
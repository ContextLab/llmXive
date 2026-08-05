import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import math
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analysis.metrics import (
    OnlineStatsAccumulator,
    MultiSeedAccumulator,
    compute_convergence_metrics,
    aggregate_multiple_seeds
)

class TestOnlineStatsAccumulator:
    def test_single_update(self):
        acc = OnlineStatsAccumulator("test_metric")
        acc.update(5.0)
        assert acc.get_mean() == 5.0
        assert acc.get_variance() == 0.0
        assert acc.count == 1

    def test_multiple_updates(self):
        acc = OnlineStatsAccumulator("test_metric")
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        for v in values:
            acc.update(v)
        
        # Mean should be 3.0
        assert math.isclose(acc.get_mean(), 3.0, rel_tol=1e-5)
        # Variance (sample) should be 2.5
        assert math.isclose(acc.get_variance(), 2.5, rel_tol=1e-5)
        assert acc.count == 5

    def test_empty_accumulator(self):
        acc = OnlineStatsAccumulator("test_metric")
        assert acc.get_mean() == 0.0
        assert acc.get_variance() == 0.0

class TestComputeConvergenceMetrics:
    def test_converges(self):
        # Create a curve that crosses 0.8 threshold
        curve = [0.1, 0.3, 0.5, 0.7, 0.85, 0.9]
        metrics = compute_convergence_metrics(curve, threshold=0.8)
        assert metrics["steps_to_threshold"] == 4
        assert metrics["final_accuracy"] == 0.9
        assert metrics["max_accuracy"] == 0.9

    def test_never_converges(self):
        curve = [0.1, 0.2, 0.3]
        metrics = compute_convergence_metrics(curve, threshold=0.8)
        assert metrics["steps_to_threshold"] == -1
        assert metrics["final_accuracy"] == 0.3

    def test_empty_curve(self):
        metrics = compute_convergence_metrics([])
        assert metrics["steps_to_threshold"] == -1
        assert metrics["final_accuracy"] == 0.0

class TestAggregateMultipleSeeds:
    def test_aggregation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "agg.json"
            seed_data = [
                {"acc": [0.5, 0.6]},
                {"acc": [0.5, 0.7]}
            ]
            
            result = aggregate_multiple_seeds(seed_data, output_path)
            
            assert "acc" in result["metrics"]
            # Mean of [0.5, 0.6, 0.5, 0.7] = 2.3 / 4 = 0.575
            assert math.isclose(result["metrics"]["acc"]["mean"], 0.575, rel_tol=1e-5)
            assert result["seeds_aggregated"] == 2

            # Verify file exists
            assert output_path.exists()
            with open(output_path) as f:
                saved = json.load(f)
            assert saved["metrics"]["acc"]["mean"] == 0.575

class TestMultiSeedAccumulator:
    def test_checkpoint_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_path = Path(tmpdir) / "checkpoint.json"
            agg = MultiSeedAccumulator(checkpoint_path, checkpoint_interval=2)
            
            # Trigger a checkpoint
            agg.update(0, "m1", 1.0)
            agg.update(1, "m1", 2.0)
            
            assert checkpoint_path.exists()
            
            with open(checkpoint_path) as f:
                data = json.load(f)
            
            assert data["metrics"]["m1"]["count"] == 2
            assert data["seeds_processed"] == 0

    def test_memory_efficiency_simulation(self):
        """
        Simulate a large run to ensure we don't store raw lists.
        We verify that the accumulator only stores count, mean, M2.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_path = Path(tmpdir) / "large_run.json"
            agg = MultiSeedAccumulator(checkpoint_path, checkpoint_interval=1000)
            
            num_steps = 10000
            for i in range(num_steps):
                agg.update(i, "acc", 0.5)
            
            # The internal state should be minimal
            assert len(agg.metrics["acc"].M2) < 100 # Just a sanity check on object size
            assert agg.metrics["acc"].count == num_steps
            
            # Verify file was written
            assert checkpoint_path.exists()
            with open(checkpoint_path) as f:
                data = json.load(f)
            assert data["metrics"]["acc"]["count"] == num_steps
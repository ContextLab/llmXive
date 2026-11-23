import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import math
import sys

# Add the project root to the path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.analysis.metrics import OnlineStatsAccumulator, MultiSeedAccumulator, compute_convergence_metrics, aggregate_multiple_seeds


class TestOnlineStatsAccumulator:
    def test_init(self):
        acc = OnlineStatsAccumulator("test")
        assert acc.count == 0
        assert acc.mean == 0.0
        assert acc.M2 == 0.0
        assert acc.min_val == float('inf')
        assert acc.max_val == float('-inf')

    def test_update_single_value(self):
        acc = OnlineStatsAccumulator("test")
        acc.update(5.0)
        stats = acc.get_stats()
        assert stats["count"] == 1
        assert stats["mean"] == 5.0
        assert stats["variance"] == 0.0
        assert stats["min"] == 5.0
        assert stats["max"] == 5.0

    def test_update_multiple_values(self):
        acc = OnlineStatsAccumulator("test")
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        for v in values:
            acc.update(v)

        stats = acc.get_stats()
        assert stats["count"] == 5
        assert math.isclose(stats["mean"], 3.0)
        assert math.isclose(stats["variance"], 2.0)
        assert math.isclose(stats["std"], math.sqrt(2.0))
        assert stats["min"] == 1.0
        assert stats["max"] == 5.0

    def test_update_invalid_values(self):
        acc = OnlineStatsAccumulator("test")
        acc.update(float('nan'))
        acc.update(float('inf'))
        acc.update(10.0)
        stats = acc.get_stats()
        assert stats["count"] == 1
        assert stats["mean"] == 10.0

    def test_merge(self):
        acc1 = OnlineStatsAccumulator("test1")
        for v in [1.0, 2.0, 3.0]:
            acc1.update(v)

        acc2 = OnlineStatsAccumulator("test2")
        for v in [4.0, 5.0]:
            acc2.update(v)

        acc1.merge(acc2)
        stats = acc1.get_stats()
        assert stats["count"] == 5
        assert math.isclose(stats["mean"], 3.0)
        assert stats["min"] == 1.0
        assert stats["max"] == 5.0


class TestComputeConvergenceMetrics:
    def test_empty_curve(self):
        result = compute_convergence_metrics([])
        assert result["steps_to_threshold"] == -1
        assert result["max_accuracy"] == 0.0

    def test_reaches_threshold(self):
        curve = [0.1, 0.3, 0.5, 0.8, 0.9]
        result = compute_convergence_metrics(curve, threshold=0.8)
        assert result["steps_to_threshold"] == 3
        assert result["max_accuracy"] == 0.9
        assert result["final_accuracy"] == 0.9

    def test_does_not_reach_threshold(self):
        curve = [0.1, 0.3, 0.5, 0.6, 0.7]
        result = compute_convergence_metrics(curve, threshold=0.8)
        assert result["steps_to_threshold"] == -1
        assert result["max_accuracy"] == 0.7


class TestAggregateMultipleSeeds:
    def test_empty_list(self):
        result = aggregate_multiple_seeds([])
        assert result == {}

    def test_single_seed(self):
        curves = [[0.1, 0.5, 0.9]]
        result = aggregate_multiple_seeds(curves)
        assert result["steps_to_threshold"]["mean"] == 2
        assert result["final_accuracy"]["mean"] == 0.9

    def test_multiple_seeds(self):
        curves = [
            [0.1, 0.5, 0.9],
            [0.2, 0.6, 0.8, 0.9],
            [0.1, 0.4, 0.7, 0.9]
        ]
        result = aggregate_multiple_seeds(curves)
        assert result["steps_to_threshold"]["count"] == 3  # All reach threshold
        assert result["final_accuracy"]["mean"] == 0.9


class TestMultiSeedAccumulator:
    def test_init(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "test.json"
            acc = MultiSeedAccumulator(path, checkpoint_interval=5)
            assert acc.checkpoint_interval == 5
            assert acc.total_steps_processed == 0
            assert acc.metrics == {}

    def test_update_and_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "test.json"
            acc = MultiSeedAccumulator(path, checkpoint_interval=5)

            # Update 10 times (should trigger checkpoint at 5 and 10)
            for i in range(10):
                acc.update("accuracy", seed=1, value=float(i))

            assert path.exists()
            with open(path, 'r') as f:
                data = json.load(f)
            assert data["total_steps_processed"] == 10
            assert "1" in data["metrics"]["accuracy"]

    def test_load_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "test.json"
            acc1 = MultiSeedAccumulator(path, checkpoint_interval=1)
            acc1.update("accuracy", seed=1, value=1.0)
            acc1.update("accuracy", seed=1, value=2.0)
            acc1.finalize()

            acc2 = MultiSeedAccumulator(path)
            loaded = acc2.load_checkpoint()
            assert loaded is True
            assert acc2.total_steps_processed == 2
            assert 1 in acc2.step_counts

    def test_get_global_stats(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "test.json"
            acc = MultiSeedAccumulator(path, checkpoint_interval=100)

            acc.update("accuracy", seed=1, value=0.5)
            acc.update("accuracy", seed=1, value=0.6)
            acc.update("accuracy", seed=2, value=0.7)
            acc.update("accuracy", seed=2, value=0.8)

            stats = acc.get_global_stats("accuracy")
            assert stats["count"] == 4
            assert math.isclose(stats["mean"], 0.65)

    def test_nonexistent_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "nonexistent.json"
            acc = MultiSeedAccumulator(path)
            loaded = acc.load_checkpoint()
            assert loaded is False

    def test_finalize(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "test.json"
            acc = MultiSeedAccumulator(path, checkpoint_interval=100)
            acc.update("accuracy", seed=1, value=1.0)
            acc.finalize()
            assert path.exists()
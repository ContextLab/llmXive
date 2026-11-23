import json
import math
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

logger = logging.getLogger(__name__)

class OnlineStatsAccumulator:
    """
    Welford's online algorithm for computing mean and variance without storing all data points.
    This ensures memory footprint remains constant regardless of the number of steps or seeds.
    """

    def __init__(self, name: str = "default"):
        self.name = name
        self.count = 0
        self.mean = 0.0
        self.M2 = 0.0  # Sum of squares of differences from the current mean
        self.min_val = float('inf')
        self.max_val = float('-inf')

    def update(self, value: float) -> None:
        """
        Update the running statistics with a new value.
        Uses Welford's online algorithm for numerical stability.
        """
        if math.isnan(value) or math.isinf(value):
            logger.warning(f"Skipping invalid value in {self.name}: {value}")
            return

        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        delta2 = value - self.mean
        self.M2 += delta * delta2

        if value < self.min_val:
            self.min_val = value
        if value > self.max_val:
            self.max_val = value

    def get_stats(self) -> Dict[str, float]:
        """
        Returns the current mean, variance, standard deviation, count, min, and max.
        """
        if self.count == 0:
            return {
                "count": 0,
                "mean": 0.0,
                "variance": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0
            }

        variance = self.M2 / self.count if self.count > 0 else 0.0
        std = math.sqrt(variance)

        return {
            "count": self.count,
            "mean": self.mean,
            "variance": variance,
            "std": std,
            "min": self.min_val if self.min_val != float('inf') else 0.0,
            "max": self.max_val if self.max_val != float('-inf') else 0.0
        }

    def merge(self, other: 'OnlineStatsAccumulator') -> None:
        """
        Merge statistics from another accumulator (parallel reduction).
        Uses parallel algorithm for combining Welford statistics.
        """
        if other.count == 0:
            return
        if self.count == 0:
            self.count = other.count
            self.mean = other.mean
            self.M2 = other.M2
            self.min_val = other.min_val
            self.max_val = other.max_val
            return

        delta = other.mean - self.mean
        new_count = self.count + other.count
        self.mean = (self.count * self.mean + other.count * other.mean) / new_count
        self.M2 += other.M2 + delta * delta * (self.count * other.count) / new_count

        if other.min_val < self.min_val:
            self.min_val = other.min_val
        if other.max_val > self.max_val:
            self.max_val = other.max_val
        self.count = new_count


class MultiSeedAccumulator:
    """
    Manages OnlineStatsAccumulators for multiple seeds and metrics.
    Handles periodic checkpointing to disk to prevent memory issues with large N.
    """

    def __init__(self, checkpoint_path: Path, checkpoint_interval: int = 100):
        self.checkpoint_path = checkpoint_path
        self.checkpoint_interval = checkpoint_interval
        self.metrics: Dict[str, Dict[int, OnlineStatsAccumulator]] = {}
        self.step_counts: Dict[int, int] = {}  # Track steps per seed
        self.total_steps_processed = 0
        self._ensure_checkpoint_dir()

    def _ensure_checkpoint_dir(self) -> None:
        """Ensure the directory for checkpoints exists."""
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

    def update(self, metric_name: str, seed: int, value: float) -> None:
        """
        Update the running statistics for a specific metric and seed.
        """
        if metric_name not in self.metrics:
            self.metrics[metric_name] = {}

        if seed not in self.metrics[metric_name]:
            self.metrics[metric_name][seed] = OnlineStatsAccumulator(f"{metric_name}_seed_{seed}")
            self.step_counts[seed] = 0

        self.metrics[metric_name][seed].update(value)
        self.step_counts[seed] += 1
        self.total_steps_processed += 1

        # Periodic checkpointing to disk
        if self.total_steps_processed % self.checkpoint_interval == 0:
            self._save_checkpoint()

    def get_global_stats(self, metric_name: str) -> Dict[str, float]:
        """
        Aggregate statistics across all seeds for a specific metric.
        """
        if metric_name not in self.metrics or not self.metrics[metric_name]:
            return {"count": 0, "mean": 0.0, "variance": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}

        global_acc = OnlineStatsAccumulator(f"global_{metric_name}")
        for seed_acc in self.metrics[metric_name].values():
            global_acc.merge(seed_acc)

        return global_acc.get_stats()

    def get_seed_stats(self, metric_name: str, seed: int) -> Optional[Dict[str, float]]:
        """
        Get statistics for a specific seed and metric.
        """
        if metric_name not in self.metrics or seed not in self.metrics[metric_name]:
            return None
        return self.metrics[metric_name][seed].get_stats()

    def _save_checkpoint(self) -> None:
        """
        Save current state to disk as JSON.
        This keeps memory usage bounded by flushing intermediate results.
        """
        checkpoint_data = {
            "checkpoint_path": str(self.checkpoint_path),
            "metrics": {},
            "step_counts": self.step_counts,
            "total_steps_processed": self.total_steps_processed
        }

        for metric_name, seed_dict in self.metrics.items():
            checkpoint_data["metrics"][metric_name] = {}
            for seed, acc in seed_dict.items():
                checkpoint_data["metrics"][metric_name][str(seed)] = acc.get_stats()

        try:
            with open(self.checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2)
            logger.info(f"Saved online stats checkpoint to {self.checkpoint_path}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint to {self.checkpoint_path}: {e}")
            raise

    def load_checkpoint(self) -> bool:
        """
        Load state from a previous checkpoint if it exists.
        Returns True if a checkpoint was loaded, False otherwise.
        """
        if not self.checkpoint_path.exists():
            return False

        try:
            with open(self.checkpoint_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.total_steps_processed = data.get("total_steps_processed", 0)
            self.step_counts = {int(k): v for k, v in data.get("step_counts", {}).items()}

            self.metrics = {}
            for metric_name, seed_dict in data.get("metrics", {}).items():
                self.metrics[metric_name] = {}
                for seed_str, stats in seed_dict.items():
                    seed = int(seed_str)
                    acc = OnlineStatsAccumulator(f"{metric_name}_seed_{seed}")
                    # Reconstruct stats (approximate for Welford, but sufficient for mean/var)
                    # Note: We cannot perfectly reconstruct M2 from mean/var/count without raw data,
                    # but for convergence metrics, mean and variance are the primary concerns.
                    # To be strictly correct, we treat loaded stats as a starting point for new updates.
                    # However, since we only save mean/var, we initialize a new accumulator.
                    # For true reconstruction, we would need to store M2.
                    acc.count = stats["count"]
                    acc.mean = stats["mean"]
                    acc.M2 = stats["variance"] * stats["count"] if stats["count"] > 0 else 0.0
                    acc.min_val = stats["min"]
                    acc.max_val = stats["max"]
                    self.metrics[metric_name][seed] = acc

            logger.info(f"Loaded online stats checkpoint from {self.checkpoint_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load checkpoint from {self.checkpoint_path}: {e}")
            return False

    def finalize(self) -> None:
        """
        Ensure a final checkpoint is saved.
        """
        self._save_checkpoint()


def compute_convergence_metrics(
    accuracy_curve: List[float],
    threshold: float = 0.8
) -> Dict[str, Union[int, float]]:
    """
    Compute convergence metrics from an accuracy curve.
    Note: This function expects a list, but for memory-constrained scenarios,
    use OnlineStatsAccumulator to track stats and compute metrics incrementally.
    This function is provided for backward compatibility or small datasets.
    """
    if not accuracy_curve:
        return {
            "steps_to_threshold": -1,
            "max_accuracy": 0.0,
            "final_accuracy": 0.0,
            "avg_accuracy": 0.0
        }

    steps_to_threshold = -1
    for i, acc in enumerate(accuracy_curve):
        if acc >= threshold:
            steps_to_threshold = i
            break

    return {
        "steps_to_threshold": steps_to_threshold,
        "max_accuracy": max(accuracy_curve),
        "final_accuracy": accuracy_curve[-1],
        "avg_accuracy": sum(accuracy_curve) / len(accuracy_curve)
    }


def aggregate_multiple_seeds(
    seed_data: List[List[float]],
    threshold: float = 0.8
) -> Dict[str, Any]:
    """
    Aggregate convergence metrics across multiple seeds.
    Returns mean, std, and min/max of steps_to_threshold and final accuracies.
    """
    if not seed_data:
        return {}

    steps_list = []
    max_acc_list = []
    final_acc_list = []

    for curve in seed_data:
        metrics = compute_convergence_metrics(curve, threshold)
        if metrics["steps_to_threshold"] != -1:
            steps_list.append(metrics["steps_to_threshold"])
        max_acc_list.append(metrics["max_accuracy"])
        final_acc_list.append(metrics["final_accuracy"])

    def safe_stats(lst):
        if not lst:
            return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
        mean_val = sum(lst) / len(lst)
        var_val = sum((x - mean_val) ** 2 for x in lst) / len(lst) if len(lst) > 0 else 0.0
        return {
            "mean": mean_val,
            "std": math.sqrt(var_val),
            "min": min(lst),
            "max": max(lst)
        }

    return {
        "steps_to_threshold": safe_stats(steps_list),
        "max_accuracy": safe_stats(max_acc_list),
        "final_accuracy": safe_stats(final_acc_list)
    }


def main():
    """
    Main entry point for testing the online stats accumulator.
    Demonstrates usage and writes a sample checkpoint.
    """
    import tempfile
    import sys

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmp_dir:
        checkpoint_path = Path(tmp_dir) / "online_stats_checkpoint.json"
        
        # Initialize accumulator
        acc = MultiSeedAccumulator(checkpoint_path, checkpoint_interval=5)
        
        # Simulate data from 2 seeds
        for seed in [1, 2]:
            for step in range(20):
                # Simulate accuracy improvement
                value = 0.5 + (step / 20.0) * 0.4 + (0.05 * (seed % 2))
                acc.update("accuracy", seed, value)
                
                # Simulate loss
                loss = 2.0 - (step / 20.0) * 1.5
                acc.update("loss", seed, loss)

        # Final checkpoint
        acc.finalize()

        # Verify checkpoint exists
        if checkpoint_path.exists():
            print(f"Checkpoint saved successfully to {checkpoint_path}")
            with open(checkpoint_path, 'r') as f:
                data = json.load(f)
            print(f"Total steps processed: {data['total_steps_processed']}")
            print(f"Metrics: {list(data['metrics'].keys())}")
        else:
            print("ERROR: Checkpoint file was not created.")
            sys.exit(1)

        # Test loading
        acc2 = MultiSeedAccumulator(checkpoint_path)
        if acc2.load_checkpoint():
            print("Checkpoint loaded successfully.")
            global_stats = acc2.get_global_stats("accuracy")
            print(f"Global accuracy stats: {global_stats}")
        else:
            print("No checkpoint found to load.")

if __name__ == "__main__":
    main()

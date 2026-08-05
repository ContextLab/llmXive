import json
import math
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import numpy as np

logger = logging.getLogger(__name__)

class OnlineStatsAccumulator:
    """
    Welford's online algorithm for computing mean and variance without storing all data points.
    This ensures memory footprint remains constant regardless of the number of steps or seeds.
    """
    def __init__(self, metric_name: str):
        self.metric_name = metric_name
        self.count = 0
        self.mean = 0.0
        self.M2 = 0.0  # Sum of squares of differences from the mean

    def update(self, value: float):
        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        delta2 = value - self.mean
        self.M2 += delta * delta2

    def get_mean(self) -> float:
        if self.count == 0:
            return 0.0
        return self.mean

    def get_variance(self) -> float:
        if self.count < 2:
            return 0.0
        return self.M2 / (self.count - 1)

    def get_std(self) -> float:
        return math.sqrt(self.get_variance())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric": self.metric_name,
            "count": self.count,
            "mean": self.mean,
            "variance": self.get_variance(),
            "std": self.get_std()
        }

class MultiSeedAccumulator:
    """
    Aggregates online statistics across multiple seeds for a single metric.
    Stores only the aggregate statistics (mean, variance) and checkpoint state,
    not the raw history of every seed.
    """
    def __init__(self, output_path: Union[str, Path], checkpoint_interval: int = 50):
        self.output_path = Path(output_path)
        self.checkpoint_interval = checkpoint_interval
        self.metrics: Dict[str, OnlineStatsAccumulator] = {}
        self.total_steps = 0
        self.step_count_since_checkpoint = 0
        self.seeds_processed = 0

    def update(self, step: int, metric_name: str, value: float):
        """Update the running statistics for a specific metric at a given step."""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = OnlineStatsAccumulator(metric_name)
        
        self.metrics[metric_name].update(value)
        self.total_steps = step
        self.step_count_since_checkpoint += 1

        if self.step_count_since_checkpoint >= self.checkpoint_interval:
            self._save_checkpoint()
            self.step_count_since_checkpoint = 0

    def finish_seed(self):
        """Call when a full seed run is complete."""
        self.seeds_processed += 1
        self._save_checkpoint()

    def _save_checkpoint(self):
        """Save intermediate statistics to disk to prevent memory bloat."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "total_steps": self.total_steps,
            "seeds_processed": self.seeds_processed,
            "metrics": {}
        }

        for name, acc in self.metrics.items():
            data["metrics"][name] = acc.to_dict()

        with open(self.output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved online stats checkpoint to {self.output_path}")

    def get_final_stats(self) -> Dict[str, Dict[str, Any]]:
        """Return the final aggregated statistics."""
        return {name: acc.to_dict() for name, acc in self.metrics.items()}

def compute_convergence_metrics(
    accuracy_curve: List[float],
    threshold: float = 0.8,
    window_size: int = 5
) -> Dict[str, float]:
    """
    Compute convergence metrics from a list of accuracy values.
    Note: This function expects a completed curve (loaded from disk or small enough to fit in memory).
    For massive curves, use OnlineStatsAccumulator during training.
    """
    if not accuracy_curve:
        return {"steps_to_threshold": -1, "final_accuracy": 0.0, "max_accuracy": 0.0}

    final_accuracy = accuracy_curve[-1]
    max_accuracy = max(accuracy_curve)
    
    steps_to_threshold = -1
    window_sum = 0.0
    for i, acc in enumerate(accuracy_curve):
        if i >= window_size - 1:
            window_sum = sum(accuracy_curve[i - window_size + 1: i + 1])
            avg_acc = window_sum / window_size
            if avg_acc >= threshold:
                steps_to_threshold = i
                break
    
    return {
        "steps_to_threshold": steps_to_threshold,
        "final_accuracy": final_accuracy,
        "max_accuracy": max_accuracy
    }

def aggregate_multiple_seeds(
    seed_results: List[Dict[str, List[float]]],
    output_path: Union[str, Path]
) -> Dict[str, Any]:
    """
    Aggregate results from multiple seeds into a single summary.
    Expects seed_results to be a list of dicts: [{metric_name: [values]}, ...]
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not seed_results:
        logger.warning("No seed results provided for aggregation.")
        return {}

    # Initialize accumulators dynamically based on the first seed's keys
    accumulators: Dict[str, OnlineStatsAccumulator] = {}
    
    for seed_data in seed_results:
        for metric_name, values in seed_data.items():
            if metric_name not in accumulators:
                accumulators[metric_name] = OnlineStatsAccumulator(metric_name)
            for val in values:
                accumulators[metric_name].update(val)

    result = {
        "metrics": {},
        "seeds_aggregated": len(seed_results)
    }

    for name, acc in accumulators.items():
        result["metrics"][name] = acc.to_dict()

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Aggregated {len(seed_results)} seeds to {output_path}")
    return result

def main():
    """
    CLI entry point for testing the online stats accumulator.
    Simulates a training run with multiple seeds and verifies checkpointing.
    """
    import tempfile
    import sys

    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint_path = Path(tmpdir) / "online_stats_checkpoint.json"
        
        print(f"Testing OnlineStatsAccumulator with checkpoint path: {checkpoint_path}")
        
        # Simulate 10 seeds, 100 steps each
        num_seeds = 10
        steps_per_seed = 100
        
        agg = MultiSeedAccumulator(checkpoint_path, checkpoint_interval=20)
        
        for seed in range(num_seeds):
            # Simulate accuracy curve for a seed
            for step in range(steps_per_seed):
                # Fake a realistic accuracy curve (logistic-like)
                acc = 0.5 + 0.4 * (1 / (1 + math.exp(-(step - 40) / 10)))
                # Add some noise
                acc += np.random.normal(0, 0.02)
                acc = max(0.0, min(1.0, acc))
                
                agg.update(step, "accuracy", acc)
                agg.update(step, "loss", 1.0 - acc)
            
            agg.finish_seed()
            print(f"Finished seed {seed + 1}/{num_seeds}")

        # Verify the file exists and is valid JSON
        if not checkpoint_path.exists():
            print("ERROR: Checkpoint file was not created.")
            sys.exit(1)
        
        with open(checkpoint_path) as f:
            data = json.load(f)
        
        print(f"Final Checkpoint Data: {json.dumps(data, indent=2)}")
        
        assert "metrics" in data
        assert "accuracy" in data["metrics"]
        assert data["seeds_processed"] == num_seeds
        assert data["metrics"]["accuracy"]["count"] == num_seeds * steps_per_seed
        
        print("SUCCESS: Online stats accumulator working correctly.")

if __name__ == "__main__":
    main()

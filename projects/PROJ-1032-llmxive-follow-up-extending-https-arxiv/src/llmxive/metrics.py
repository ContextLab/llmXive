"""
Real-time reward and gradient norm monitoring for the llmXive asynchronous RL pipeline.

This module provides utilities to track, aggregate, and report training metrics
including reward values and gradient norms during the training loop.

Excludes baseline loading logic (handled by baseline_loader.py).
"""
import logging
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import deque
import torch
import numpy as np

from src.llmxive.exceptions import DATA_INTEGRITY_ERROR

logger = logging.getLogger(__name__)


@dataclass
class MetricSnapshot:
    """A single snapshot of metrics at a training step."""
    step: int
    reward: float
    grad_norm: float
    timestamp: float
    staleness_level: int
    memory_usage_mb: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MetricsMonitor:
    """
    Monitors and aggregates real-time training metrics.
    
    Tracks reward values and gradient norms, computes rolling statistics,
    and detects potential divergence based on threshold violations.
    """

    def __init__(
        self,
        buffer_size: int = 1000,
        staleness_level: int = 0,
        model_id: str = "unknown"
    ):
        """
        Initialize the metrics monitor.
        
        Args:
            buffer_size: Maximum number of recent metrics to store for rolling stats.
            staleness_level: Current staleness configuration for this run.
            model_id: Identifier for the model being trained.
        """
        self.buffer_size = buffer_size
        self.staleness_level = staleness_level
        self.model_id = model_id
        
        # Rolling buffers for recent metrics
        self._rewards: deque = deque(maxlen=buffer_size)
        self._grad_norms: deque = deque(maxlen=buffer_size)
        self._steps: deque = deque(maxlen=buffer_size)
        self._timestamps: deque = deque(maxlen=buffer_size)
        
        # Full history for final analysis
        self._history: List[MetricSnapshot] = []
        
        # Running totals for global stats
        self._total_reward = 0.0
        self._total_grad_norm = 0.0
        self._step_count = 0
        self._start_time = time.time()

    def record(
        self,
        step: int,
        reward: float,
        grad_norm: float,
        memory_usage_mb: Optional[float] = None
    ) -> None:
        """
        Record a new metric snapshot.
        
        Args:
            step: Current training step.
            reward: Reward value obtained at this step.
            grad_norm: Gradient norm at this step.
            memory_usage_mb: Optional memory usage in MB.
        
        Raises:
            DATA_INTEGRITY_ERROR: If reward or grad_norm are NaN or Inf.
        """
        # Validate inputs
        if not np.isfinite(reward):
            raise DATA_INTEGRITY_ERROR(f"Invalid reward value at step {step}: {reward}")
        if not np.isfinite(grad_norm):
            raise DATA_INTEGRITY_ERROR(f"Invalid gradient norm at step {step}: {grad_norm}")

        snapshot = MetricSnapshot(
            step=step,
            reward=float(reward),
            grad_norm=float(grad_norm),
            timestamp=time.time(),
            staleness_level=self.staleness_level,
            memory_usage_mb=memory_usage_mb
        )

        # Update rolling buffers
        self._rewards.append(snapshot.reward)
        self._grad_norms.append(snapshot.grad_norm)
        self._steps.append(snapshot.step)
        self._timestamps.append(snapshot.timestamp)

        # Append to full history
        self._history.append(snapshot)

        # Update running totals
        self._total_reward += snapshot.reward
        self._total_grad_norm += snapshot.grad_norm
        self._step_count += 1

    def get_rolling_stats(self, window_size: Optional[int] = None) -> Dict[str, float]:
        """
        Compute rolling statistics over recent metrics.
        
        Args:
            window_size: Number of recent steps to consider. Defaults to buffer_size.
        
        Returns:
            Dictionary containing mean and std for reward and grad_norm.
        """
        if window_size is None:
            window_size = self.buffer_size
        
        # Use the most recent window_size entries
        recent_rewards = list(self._rewards)[-window_size:] if self._rewards else []
        recent_grads = list(self._grad_norms)[-window_size:] if self._grads else []

        if not recent_rewards or not recent_grads:
            return {
                "reward_mean": 0.0,
                "reward_std": 0.0,
                "grad_norm_mean": 0.0,
                "grad_norm_std": 0.0,
                "window_size": 0
            }

        return {
            "reward_mean": float(np.mean(recent_rewards)),
            "reward_std": float(np.std(recent_rewards)),
            "grad_norm_mean": float(np.mean(recent_grads)),
            "grad_norm_std": float(np.std(recent_grads)),
            "window_size": len(recent_rewards)
        }

    def get_global_stats(self) -> Dict[str, Any]:
        """
        Compute global statistics over all recorded metrics.
        
        Returns:
            Dictionary containing total steps, mean reward, mean grad norm,
            and total elapsed time.
        """
        if self._step_count == 0:
            return {
                "total_steps": 0,
                "mean_reward": 0.0,
                "mean_grad_norm": 0.0,
                "total_reward": 0.0,
                "total_grad_norm": 0.0,
                "elapsed_time_seconds": 0.0
            }

        elapsed = time.time() - self._start_time
        return {
            "total_steps": self._step_count,
            "mean_reward": self._total_reward / self._step_count,
            "mean_grad_norm": self._total_grad_norm / self._step_count,
            "total_reward": self._total_reward,
            "total_grad_norm": self._total_grad_norm,
            "elapsed_time_seconds": elapsed
        }

    def get_latest(self) -> Optional[MetricSnapshot]:
        """Return the most recent metric snapshot."""
        return self._history[-1] if self._history else None

    def export_history(self) -> List[Dict[str, Any]]:
        """Export the full history as a list of dictionaries."""
        return [s.to_dict() for s in self._history]

    def save_to_json(self, filepath: str) -> None:
        """
        Save the full metrics history to a JSON file.
        
        Args:
            filepath: Path to the output JSON file.
        """
        data = {
            "model_id": self.model_id,
            "staleness_level": self.staleness_level,
            "global_stats": self.get_global_stats(),
            "history": self.export_history()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Metrics saved to {filepath}")


def compute_gradient_norm_from_params(params: List[torch.nn.Parameter]) -> float:
    """
    Compute the L2 norm of gradients across all parameters.
    
    Args:
        params: List of torch.nn.Parameter objects that have gradients computed.
    
    Returns:
        The L2 norm of the concatenated gradients.
    
    Raises:
        DATA_INTEGRITY_ERROR: If any parameter has no gradient.
    """
    total_norm = 0.0
    count = 0
    for p in params:
        if p.grad is None:
            # Skip parameters without gradients (common in frozen layers)
            continue
        if not torch.isfinite(p.grad).all():
            raise DATA_INTEGRITY_ERROR(f"Non-finite gradient detected in parameter {count}")
        total_norm += p.grad.data.norm(2).item() ** 2
        count += 1
    
    if count == 0:
        return 0.0
    
    return total_norm ** 0.5


def log_metrics_step(
    monitor: MetricsMonitor,
    step: int,
    reward: float,
    grad_norm: float,
    memory_mb: Optional[float] = None
) -> None:
    """
    Convenience function to record metrics and log them.
    
    Args:
        monitor: The MetricsMonitor instance.
        step: Current training step.
        reward: Reward value.
        grad_norm: Gradient norm.
        memory_mb: Optional memory usage in MB.
    """
    monitor.record(step, reward, grad_norm, memory_mb)
    latest = monitor.get_latest()
    if latest:
        logger.info(
            f"Step {step}: reward={latest.reward:.4f}, "
            f"grad_norm={latest.grad_norm:.4f}, "
            f"staleness={latest.staleness_level}"
        )
        if memory_mb is not None:
            logger.info(f"  Memory usage: {memory_mb:.2f} MB")
            if memory_mb > 6500:
                logger.warning(f"Memory usage ({memory_mb:.2f} MB) exceeds 6.5 GB threshold!")
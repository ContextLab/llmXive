"""Metrics tracking for real-time reward and gradient monitoring."""
import json
import time
from typing import List, Dict, Any
from pathlib import Path

class MetricsTracker:
    """Track and log training metrics."""
    
    def __init__(self, log_path: str):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.metrics: List[Dict[str, Any]] = []
        self.start_time = time.time()
    
    def log_step(self, step: int, reward: float, grad_norm: float, staleness: int = 0):
        """Log a single training step."""
        entry = {
            "step": step,
            "reward": float(reward),
            "grad_norm": float(grad_norm),
            "staleness": staleness,
            "elapsed_seconds": time.time() - self.start_time
        }
        self.metrics.append(entry)
    
    def save(self):
        """Save metrics to JSON file."""
        with open(self.log_path, 'w') as f:
            json.dump(self.metrics, f, indent=2)
    
    def get_reward_curve(self) -> List[float]:
        """Get the sequence of rewards."""
        return [m["reward"] for m in self.metrics]
    
    def get_grad_norms(self) -> List[float]:
        """Get the sequence of gradient norms."""
        return [m["grad_norm"] for m in self.metrics]
